"""OMIM ingest to generate RDF .ttl

Resources
- https://monarch-initiative.github.io/monarch-ingest/Sources/OMIM/

Steps
- Loads prefixes
- Parses mimTitles.txt
  A tab-delimited file of MIM numbers and titles.
  - Get id's, titles, and type
- Parses mim2gene.txt
  A tab-delimited file linking MIM numbers with NCBI Gene IDs, Ensembl Gene IDs, and HGNC Approved Gene Symbols.
  - for mim_number, entrez_id in gene_map.items():
    - graph.add((OMIM[mim_number], OWL.equivalentClass, NCBIGENE[entrez_id]))
  - for mim_number, entrez_id in pheno_map.items():
    - graph.add((NCBIGENE[entrez_id], RO['0002200'], OMIM[mim_number]))
- Parses mim2gene.tsv
  This was created based on mim2gene.txt. All that was changed was that comments were removed and header was
  uncommented, and file extension changed to tsv.
  - Adds HGNC symbols
- Parses phenotypicSeries.txt
  - Gets IDs and phenotype labels / descriptions
  - Gets mim numbers referenced
- Parse morbidmap.txt
    A tab-delimited file of OMIM's Synopsis of the Human Gene Map (same as genemap2.txt above) sorted alphabetically by
    disorder.
  - links omim entry (~gene) to phenotype
    - I thought phenotypic series did something like the sme?
  - links omim entry to chromosome location
- Parses BioPortal's omim.ttl
  At least, I think that's where that .ttl file comes from. Adds following info to graph:
  - pmid info
  - umls info
  - orphanet info
- Add "omim replaced" info
  - This is gotten from mimTitles.txt at beginning
- Parses mim2gene2.txt
  A tab-delimited file linking MIM numbers with NCBI Gene IDs, Ensembl Gene IDs, and HGNC Approved Gene Symbols.
  - Adds HGNC symbols
- TODO: Parses hgnc/hgnc_complete_set.txt
  A tab-delimited file with purpose unknown to me (Joe), but has mappings between HGNC symbols and IDs.
  - Get HGNC symbol::id mappings.
todo: The downloads should all happen at beginning of script

Assumptions
1. Mappings obtained from official OMIM files as described above are interpreted correctly (e.g. skos:exactMatch).
"""
import yaml
from hashlib import md5

from rdflib import Graph, RDF, OWL, RDFS, Literal, BNode, URIRef, SKOS
from rdflib.term import Identifier

from omim2obo.config import REVIEW_CASES_PATH, ROOT_DIR, GLOBAL_TERMS, ReviewCase
from omim2obo.namespaces import *
from omim2obo.parsers.omim_entry_parser import get_alt_labels, get_pubs, get_mapped_ids, LabelCleaner
from omim2obo.parsers.omim_txt_parser import *  # todo: change to specific imports


# Vars
OUTPATH = os.path.join(ROOT_DIR / 'omim.ttl')

# Logging
LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)
LOG.addHandler(logging.StreamHandler(sys.stdout))
REVIEW_CASES: List[ReviewCase] = []


# Funcs
def get_curie_maps():
    """Rectrieve CURIE to URL info"""
    map_file = DATA_DIR / 'dipper/curie_map.yaml'
    with open(map_file, "r") as f:
        maps = yaml.safe_load(f)
    return maps


def add_subclassof_restriction(graph: Graph, predicate: URIRef, some_values_from: URIRef, on: URIRef) -> BNode:
    """Creates a subClassOf someValuesFrom restriction"""
    b = BNode()
    graph.add((b, RDF['type'], OWL['Restriction']))
    graph.add((b, OWL['onProperty'], predicate))
    graph.add((b, OWL['someValuesFrom'], some_values_from))
    graph.add((on, RDFS['subClassOf'], b))
    return b


def add_subclassof_restriction_with_evidence(
    graph: Graph, predicate: URIRef, some_values_from: URIRef, on: URIRef, evidence: Union[str, Literal]
):
    """Creates a subClassOf someValuesFrom restriction, and adds an evidence axiom to it."""
    evidence = Literal(evidence) if type(evidence) is str else evidence
    # Add restriction on MIM class
    b: BNode = add_subclassof_restriction(graph, predicate, some_values_from, on)
    # Add axiom to restriction
    b2 = BNode()
    graph.add((b2, RDF['type'], OWL['Axiom']))
    graph.add((b2, OWL['annotatedSource'], on))
    graph.add((b2, OWL['annotatedProperty'], RDFS['subClassOf']))
    graph.add((b2, OWL['annotatedTarget'], b))
    graph.add((b2, BIOLINK['has_evidence'], evidence))
    graph.add((b2, RDFS['comment'], evidence))


# Classes
class DeterministicBNode(BNode):
    """Overrides BNode to create a deterministic ID"""

    def __new__(cls, source_ref: str):
        """Constructor
            source_ref: A reference to be passed to MD5 to generate _id.
        """
        _id: str = md5(source_ref.encode()).hexdigest()
        return Identifier.__new__(cls, _id)


class OmimGraph(Graph):
    """Graph w/ some additional OMIM features"""
    __instance: Graph = None

    @staticmethod
    def get_graph():
        """Retrieve graph instance"""
        if OmimGraph.__instance is None:
            OmimGraph.__instance = Graph()
            for ns_prefix, ns_uri in CURIE_MAP.items():
                OmimGraph.__instance.namespace_manager.bind(ns_prefix, URIRef(ns_uri))
        return OmimGraph.__instance


# Vars
TAX_LABEL = 'Homo sapiens'
TAX_ID = GLOBAL_TERMS[TAX_LABEL]
TAX_URI = URIRef(NCBITAXON + TAX_ID.split(':')[1])
CURIE_MAP = get_curie_maps()
label_cleaner = LabelCleaner()
CONFIG = {
    'verbose': False
}


# Main
def omim2obo(use_cache: bool = True):
    """Run program"""
    graph = OmimGraph.get_graph()
    download_files_tf: bool = not use_cache

    # Populate prefixes
    for prefix, uri in CURIE_MAP.items():
        graph.namespace_manager.bind(prefix, URIRef(uri))

    # Parse mimTitles.txt
    # - Get id's, titles, and type
    omim_type_and_titles, omim_replaced = parse_mim_titles(get_mim_file('mimTitles', download_files_tf))
    omim_types: Dict[str, str] = {k: v[0].name for k, v in omim_type_and_titles.items()}
    omim_ids = list(omim_type_and_titles.keys())

    if CONFIG['verbose']:
        LOG.info('Tot MIM numbers from mimTitles.txt: %i', len(omim_ids))
        LOG.info('Tot MIM types: %i', len(omim_type_and_titles))

    # Populate graph
    # - Non-OMIM triples
    graph.add((URIRef('http://purl.obolibrary.org/obo/mondo/omim.owl'), RDF.type, OWL.Ontology))
    graph.add((URIRef(oboInOwl.hasSynonymType), RDF.type, OWL.AnnotationProperty))
    graph.add((URIRef(MONDONS.omim_included), RDF.type, OWL.AnnotationProperty))
    graph.add((URIRef(OMO['0003000']), RDF.type, OWL.AnnotationProperty))
    graph.add((BIOLINK['has_evidence'], RDF.type, OWL.AnnotationProperty))
    graph.add((TAX_URI, RDF.type, OWL.Class))
    graph.add((TAX_URI, RDFS.label, Literal(TAX_LABEL)))

    # - OMIM triples
    for omim_id in omim_ids:
        omim_uri = OMIM[omim_id]
        graph.add((omim_uri, RDF.type, OWL.Class))

        # - Deprecated classes
        if str(omim_type_and_titles[omim_id][0]) == 'OmimType.OBSOLETE':
            graph.add((omim_uri, OWL.deprecated, Literal(True)))
            if omim_replaced.get(omim_id, None):
                label_ids = omim_replaced[omim_id]
                if len(label_ids) == 1:
                    # IAO:0100001 means: "term replaced by"
                    graph.add((omim_uri, IAO['0100001'], OMIM[label_ids[0]]))
                elif len(label_ids) > 1:
                    for replaced_mim_num in label_ids:
                        graph.add((omim_uri, oboInOwl.consider, OMIM[replaced_mim_num]))
                continue

        # - Non-deprecated
        # Parse titles
        omim_type, pref_labels_str, alt_labels, inc_labels = omim_type_and_titles[omim_id]
        other_labels = []
        cleaned_inc_labels = []
        label_endswith_included_alt = False
        label_endswith_included_inc = False
        pref_labels: List[str] = [x.strip() for x in pref_labels_str.split(';')]
        pref_title: str = pref_labels[0]
        pref_symbols: List[str] = pref_labels[1:]
        if alt_labels:
            cleaned_alt_labels, label_endswith_included_alt = get_alt_labels(alt_labels)
            other_labels += cleaned_alt_labels
        if inc_labels:
            cleaned_inc_labels, label_endswith_included_inc = get_alt_labels(inc_labels)
            # other_labels += cleaned_inc_labels  # deactivated 7/2024 in favor of alternative for tagging 'included'

        # Special cases depending on OMIM term type
        is_gene = omim_type == OmimType.GENE or omim_type == OmimType.HAS_AFFECTED_FEATURE
        if omim_type == OmimType.HERITABLE_PHENOTYPIC_MARKER:  # '%' char
            graph.add((omim_uri, BIOLINK['category'], BIOLINK['Disease']))
        elif is_gene:  # * or + chars
            graph.add((omim_uri, RDFS.subClassOf, SO['0000704']))  # gene
            graph.add((omim_uri, MONDO.exclusionReason, MONDO.nonDisease))
            graph.add((omim_uri, BIOLINK['category'], BIOLINK['Gene']))
        elif omim_type == OmimType.PHENOTYPE:  # '#' char
            graph.add((omim_uri, BIOLINK['category'], BIOLINK['Disease']))  # phenotype ~= disease
        elif omim_type == OmimType.SUSPECTED:  # NULL
            graph.add((omim_uri, MONDO.exclusionReason, MONDO.excludeTrait))

        # Alternative rdfs:label for genes
        if is_gene and pref_symbols:
            gene_label_err = 'Warning: Only 1 symbol picked for label for gene term, but there were 2 to choose ' \
                 f'from. Unsure which is best. Picking the first.\nhttps://omim.org/entry/{omim_id} - {pref_symbols}'
            if len(pref_symbols) > 1:
                LOG.warning(gene_label_err)  # todo: decide the best way to handle these situations
            graph.add((omim_uri, RDFS.label, Literal(pref_symbols[0])))
        else:
            graph.add((omim_uri, RDFS.label, Literal(label_cleaner.clean(pref_title))))

        # todo: .clean()/.cleanup_label() 2nd param `explicit_abbrev` should be List[str] instead of str. And below,
        #  should pass all symbols/abbrevs from each of preferred, alt, included each time it is called. If no symbols
        #  for given term, should pass empty list. See: https://github.com/monarch-initiative/omim/issues/129
        abbrev: Union[str, None] = None if not pref_symbols else pref_symbols[0]

        # Add synonyms
        graph.add((omim_uri, oboInOwl.hasExactSynonym, Literal(label_cleaner.clean(pref_title, abbrev))))
        for alt_label in other_labels:
            graph.add((omim_uri, oboInOwl.hasExactSynonym, Literal(label_cleaner.clean(alt_label, abbrev))))
        for abbreviation in pref_symbols:
            graph.add((omim_uri, oboInOwl.hasExactSynonym, Literal(abbreviation)))
            # Reify on abbreviations. See: https://github.com/monarch-initiative/omim/issues/2
            axiom = BNode()
            graph.add((axiom, RDF.type, OWL.Axiom))
            graph.add((axiom, OWL.annotatedSource, omim_uri))
            graph.add((axiom, OWL.annotatedProperty, oboInOwl.hasExactSynonym))
            graph.add((axiom, OWL.annotatedTarget, Literal(abbreviation)))
            graph.add((axiom, oboInOwl.hasSynonymType, OMO['0003000']))

        # Add 'included' entry properties
        included_detected_comment = "This term has one or more labels that end with ', INCLUDED'."
        if label_endswith_included_alt or label_endswith_included_inc:
            graph.add((omim_uri, RDFS['comment'], Literal(included_detected_comment)))
        for included_label in cleaned_inc_labels:
            graph.add((omim_uri, URIRef(MONDONS.omim_included), Literal(label_cleaner.clean(included_label, abbrev))))

    # Gene ID
    # Why is 'skos:exactMatch' appropriate for disease::gene relationships? - joeflack4 2022/06/06
    get_mim_file('genemap2', download_files_tf)  # dl latest file
    mim2gene_lines: List[str] = get_mim_file('mim2gene', download_files_tf)  # dl latest file & return
    gene_map, pheno_map, hgnc_map = parse_mim2gene(mim2gene_lines)
    for mim_number, entrez_id in gene_map.items():
        graph.add((OMIM[mim_number], SKOS.exactMatch, NCBIGENE[entrez_id]))
    for mim_number, entrez_id in pheno_map.items():
        # RO['0002200'] = 'has phenotype'
        add_subclassof_restriction(graph, RO['0002200'], OMIM[mim_number], NCBIGENE[entrez_id])
    hgnc_symbol_id_map: Dict[str, str] = get_hgnc_symbol_id_map()
    for mim_number, hgnc_symbol in hgnc_map.items():
        graph.add((OMIM[mim_number], SKOS.exactMatch, HGNC_symbol[hgnc_symbol]))
        if hgnc_symbol in hgnc_symbol_id_map:
            graph.add((OMIM[mim_number], SKOS.exactMatch, HGNC[hgnc_symbol_id_map[hgnc_symbol]]))

    # Phenotypic Series
    pheno_series = parse_phenotypic_series_titles(get_mim_file('phenotypicSeries', download_files_tf))
    for ps_id in pheno_series:
        graph.add((OMIMPS[ps_id], RDF.type, OWL.Class))
        graph.add((OMIMPS[ps_id], RDFS.label, Literal(pheno_series[ps_id][0])))
        # Are all phenotypes listed here indeed disease? - joeflack4 2021/11/11
        graph.add((OMIMPS[ps_id], BIOLINK.category, BIOLINK.Disease))
        for mim_number in pheno_series[ps_id][1]:
            graph.add((OMIM[mim_number], RDFS.subClassOf, OMIMPS[ps_id]))

    # Morbid map
    gene_phenotypes: Dict[str, Dict] = parse_morbid_map(get_mim_file('morbidmap', download_files_tf))

    # Gene-Chromosome relationships
    # - Cyto location: Add RO:0002525 (is subsequence of)
    # https://www.ebi.ac.uk/ols/ontologies/ro/properties?iri=http://purl.obolibrary.org/obo/RO_0002525
    for gene_mim, gene_data in gene_phenotypes.items():
        if gene_data['cyto_location']:
            chr_id = '9606chr' + gene_data['cyto_location']  # 9606: NCBI Taxonomy ID for Homo Sapiens
            add_subclassof_restriction(graph, RO['0002525'], CHR[chr_id], OMIM[gene_mim])

    # Disease->Gene (& more Gene->Disease) relationships
    # - Collect phenotype MIMs & associated gene MIMs and relationship info
    phenotype_genes: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    for gene_mim, gene_data in gene_phenotypes.items():
        for assoc in gene_data['phenotype_associations']:
            p_mim, p_lab, p_map_key, p_map_lab = assoc['phenotype_mim_number'], assoc['phenotype_label'], \
                assoc['phenotype_mapping_info_key'], assoc['phenotype_mapping_info_label']
            if not p_mim:  # not an association to another MIM; ignore
                continue  # see: https://github.com/monarch-initiative/omim/issues/78
            phenotype_genes[p_mim].append({
                'gene_id': gene_mim, 'phenotype_label': p_lab, 'mapping_key': p_map_key, 'mapping_label': p_map_lab})

    self_ref_case = 0
    self_ref_rows: List[Dict] = []
    # - Add relations (subclass restrictions)
    for p_mim, assocs in phenotype_genes.items():
        for assoc in assocs:
            gene_mim, p_lab, p_map_key, p_map_lab = assoc['gene_id'], assoc['phenotype_label'], \
                assoc['mapping_key'], assoc['mapping_label']
            evidence = f'Evidence: ({p_map_key}) {p_map_lab}'

            # General skippable cases
            # - not p_mim: Skip because not an association to another MIM (Provenance:
            #  https://github.com/monarch-initiative/omim/issues/78)
            # - p_map_key == '1': Skip because association w/ unknown defect (Provenance:
            #  https://github.com/monarch-initiative/omim/issues/79#issuecomment-1319408780)
            if not p_mim or p_map_key == '1':
                continue

            # Gene->Disease non-causal relationships
            # - RO:0003302 docs: see MORBIDMAP_PHENOTYPE_MAPPING_KEY_PREDICATES
            if p_map_key != '3':  # 3 = 'causal'. Handled separately below.
                g2d_pred = MORBIDMAP_PHENOTYPE_MAPPING_KEY_PREDICATES[p_map_key] if len(assocs) == 1 else RO['0003302']
                add_subclassof_restriction_with_evidence(graph, g2d_pred, OMIM[p_mim], OMIM[gene_mim], evidence)

            # Disease->Gene & Gene->Disease: Causal relationships
            # - Skip non-causal cases
            #  - 3: The molecular basis for the disorder is known; a mutation has been found in the gene.
            if len(assocs) > 1 or p_map_key != '3' or not p2g_is_definitive(p_lab):
                continue
            #  - Digenic: Should technically be none marked 'digenic' if only 1 association, but there are.
            if 'digenic' in p_lab.lower():
                # noinspection PyTypeChecker typecheck_fail_old_Python
                REVIEW_CASES.append({
                    "classCode": 1,
                    "classShortName": "causalD2gButMarkedDigenic",
                    "value": f"OMIM:{p_mim}: {p_lab} (Gene: OMIM:{gene_mim})",
                })
            p_mim_type: str = omim_types[p_mim]  # Allowable: PHENOTYPE, HERITABLE_PHENOTYPIC_MARKER (#, %)
            mim_type_err = f"Warning: Unexpected MIM type {p_mim_type} for Phenotype {p_mim} when parsing phenotype-" \
                f"disease relationships. Skipping."
            if p_mim_type in ('OBSOLETE', 'SUSPECTED', 'HAS_AFFECTED_FEATURE'):  # ^, NULL, +
                print(mim_type_err, file=sys.stderr)  # Hasn't happened. Failsafe.
            if p_mim_type == 'GENE':  # *
                print(mim_type_err, file=sys.stderr)  # OMIM recognized as data quality issue. Fixed 2024/11. Failsafe.

            def get_self_ref_assocs(_mim: str) -> List[Dict]:
                """Find any cases where it appears that there is a self-referential gene-disease association"""
                if p_mim not in gene_phenotypes:
                    return []
                _assocs = gene_phenotypes[_mim]['phenotype_associations']
                _self_ref_assocs = []
                for _assoc in _assocs:
                    if not _assoc['phenotype_mim_number']:
                        _self_ref_assocs.append(_assoc)
                return _self_ref_assocs
            self_ref_assocs: List[Dict] = get_self_ref_assocs(p_mim)
            if len(self_ref_assocs) > 1:
                raise RuntimeError('Unexpected self-referential disease-gene assoc w/ > 1 self ref')  # Failsafe. n=0
            if self_ref_assocs:
                self_ref_case += 1
                self_ref_rows.append({
                    'case': self_ref_case, 'disease': p_mim, 'disease_label': p_lab, 'map_key': p_map_key,
                    'gene': gene_mim
                })
                for ass in self_ref_assocs:
                    self_ref_rows.append({
                        'case': self_ref_case, 'disease': '', 'disease_label': ass['phenotype_label'], 'map_key':
                        ass['phenotype_mapping_info_key'], 'gene': p_mim
                    })

            # Disease --(RO:0004003 'has material basis in germline mutation in')--> Gene
            # https://www.ebi.ac.uk/ols4/ontologies/ro/properties?iri=http://purl.obolibrary.org/obo/RO_0004003
            add_subclassof_restriction_with_evidence(
                graph, RO['0004003'], OMIM[gene_mim], OMIM[p_mim], evidence)
            # Gene --(RO:0004013 'is causal germline mutation in')--> Disease
            # https://www.ebi.ac.uk/ols4/ontologies/ro/properties?iri=http://purl.obolibrary.org/obo/RO_0004013
            add_subclassof_restriction_with_evidence(
                graph, RO['0004013'], OMIM[p_mim], OMIM[gene_mim], evidence)

    self_ref_df = pd.DataFrame(self_ref_rows)
    self_ref_df.to_csv('~/Desktop/self-referential-g2d.tsv', index=False, sep='\t')

    # PUBMED, UMLS
    # How do we get these w/out relying on this ttl file? Possible? Where is it from? - joeflack4 2021/11/11
    pmid_map, umls_map, orphanet_map = get_maps_from_turtle()

    # Get the recent updated
    updated_entries = get_updated_entries()
    for entry in updated_entries:
        entry = entry['entry']
        mim_number = str(entry['mimNumber'])
        pmid_map[mim_number] = get_pubs(entry)
        external_maps = get_mapped_ids(entry)
        umls_map[mim_number] = external_maps[UMLS]
        orphanet_map[mim_number] = external_maps[ORPHANET]

    for mim_number, pm_ids in pmid_map.items():
        for pm_id in pm_ids:
            # What's IAO['0000142'] - joeflack4 2021/11/11
            graph.add((OMIM[mim_number], IAO['0000142'], PMID[pm_id]))
    for mim_number, umlsids in umls_map.items():
        for umls_id in umlsids:
            graph.add((OMIM[mim_number], SKOS.exactMatch, UMLS[umls_id]))
    for mim_number, orphanet_ids in orphanet_map.items():
        for orphanet_id in orphanet_ids:
            graph.add((OMIM[mim_number], SKOS.exactMatch, ORPHANET[orphanet_id]))

    review_df = pd.DataFrame(REVIEW_CASES)  # todo: ensure comment field exists even when no row uses
    review_df.to_csv(REVIEW_CASES_PATH, index=False, sep='\t')
    with open(OUTPATH, 'w') as f:
        f.write(graph.serialize(format='turtle'))


if __name__ == '__main__':
    omim2obo()

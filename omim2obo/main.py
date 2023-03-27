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

from omim2obo.namespaces import *
from omim2obo.parsers.omim_entry_parser import get_alt_labels, get_pubs, \
    get_mapped_ids, LabelCleaner
from omim2obo.config import ROOT_DIR, GLOBAL_TERMS
from omim2obo.parsers.omim_txt_parser import *


# Vars
OUTPATH = os.path.join(ROOT_DIR / 'omim.ttl')
ISSUES_OUTPATH = os.path.join(ROOT_DIR, 'omimIssues.json')


# Logging
LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)
LOG.addHandler(logging.StreamHandler(sys.stdout))


# Funcs
def get_curie_maps():
    """Rectrieve CURIE to URL info"""
    map_file = DATA_DIR / 'dipper/curie_map.yaml'
    with open(map_file, "r") as f:
        maps = yaml.safe_load(f)
    return maps


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
def omim2obo(use_cache: bool = False):
    """Run program"""
    issues = {}
    graph = OmimGraph.get_graph()
    download_files_tf: bool = not use_cache

    # Populate prefixes
    for prefix, uri in CURIE_MAP.items():
        graph.namespace_manager.bind(prefix, URIRef(uri))

    # Parse mimTitles.txt
    # - Get id's, titles, and type
    omim_type_and_titles, omim_replaced = parse_mim_titles(get_mim_file('mimTitles.txt', download_files_tf))
    omim_ids = list(omim_type_and_titles.keys())

    if CONFIG['verbose']:
        LOG.info('Tot MIM numbers from mimTitles.txt: %i', len(omim_ids))
        LOG.info('Tot MIM types: %i', len(omim_type_and_titles))

    # Populate graph
    # - Non-OMIM triples
    graph.add((
        URIRef('http://www.geneontology.org/formats/oboInOwl#hasSynonymType'),
        RDF.type, OWL.AnnotationProperty))
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
        omim_type, pref_label, alt_labels, inc_labels = omim_type_and_titles[omim_id]
        label = pref_label
        other_labels = []
        label_endswith_included_alt, label_endswith_included_inc = False, False
        if alt_labels:
            cleaned_alt_labels, label_endswith_included_alt = get_alt_labels(alt_labels)
            other_labels += cleaned_alt_labels
        if inc_labels:
            cleaned_inc_labels, label_endswith_included_inc = get_alt_labels(inc_labels)
            other_labels += cleaned_inc_labels

        included_detected_comment = "This term has one or more labels that end with ', INCLUDED'."
        if label_endswith_included_alt or label_endswith_included_inc:
            graph.add((omim_uri, RDFS['comment'], Literal(included_detected_comment)))

        use_abbrev_over_label = False
        abbrev = label.split(';')[1].strip() if ';' in label else None
        if omim_type == OmimType.HERITABLE_PHENOTYPIC_MARKER:  # %
            graph.add((omim_uri, BIOLINK['category'], BIOLINK['Disease']))
        elif omim_type == OmimType.GENE or omim_type == OmimType.HAS_AFFECTED_FEATURE:  # * or +
            use_abbrev_over_label = True
            graph.add((omim_uri, RDFS.subClassOf, SO['0000704']))  # gene
            graph.add((omim_uri, MONDO.exclusionReason, MONDO.nonDisease))
            graph.add((omim_uri, BIOLINK['category'], BIOLINK['Gene']))
        elif omim_type == OmimType.PHENOTYPE:
            graph.add((omim_uri, BIOLINK['category'], BIOLINK['Disease']))  # phenotype ~= disease
        elif omim_type == OmimType.SUSPECTED:
            graph.add((omim_uri, MONDO.exclusionReason, MONDO.excludeTrait))
        else:
            pass

        if use_abbrev_over_label and abbrev:
            graph.add((omim_uri, RDFS.label, Literal(abbrev)))
        else:
            graph.add((omim_uri, RDFS.label, Literal(label_cleaner.clean(label))))

        exact_labels = [s.strip() for s in label.split(';')]
        # the last string is an abbreviation. Add OWL reification. See issue #2
        if len(exact_labels) > 1:
            abbr = exact_labels.pop()
            graph.add((omim_uri, oboInOwl.hasExactSynonym, Literal(abbr)))
            axiom_id = DeterministicBNode(abbr)
            graph.add((axiom_id, RDF.type, OWL.Axiom))
            # What's CL['0017543'] - joeflack4 2021/11/11
            graph.add((axiom_id, OWL.annotatedSource, CL['0017543']))
            graph.add((axiom_id, OWL.annotatedProperty, oboInOwl.hasExactSynonym))
            graph.add((axiom_id, OWL.annotatedTarget, Literal(abbr)))
            graph.add((axiom_id, oboInOwl.hasSynonymType, MONDONS.ABBREVIATION))
        for exact_label in exact_labels:
            graph.add((omim_uri, oboInOwl.hasExactSynonym, Literal(label_cleaner.clean(exact_label, abbrev))))
        for label in other_labels:
            graph.add((omim_uri, oboInOwl.hasExactSynonym, Literal(label_cleaner.clean(label, abbrev))))

    # Gene ID
    # Why is 'skos:exactMatch' appropriate for disease::gene relationships? - joeflack4 2022/06/06
    get_mim_file('genemap2.txt', download_files_tf)  # dl latest file
    mim2gene_lines: List[str] = get_mim_file('mim2gene.txt', download_files_tf)  # dl latest file & return
    gene_map, pheno_map, hgnc_map = parse_mim2gene(mim2gene_lines)
    for mim_number, entrez_id in gene_map.items():
        graph.add((OMIM[mim_number], SKOS.exactMatch, NCBIGENE[entrez_id]))
    for mim_number, entrez_id in pheno_map.items():
        # RO['0002200'] = 'has phenotype'
        graph.add((NCBIGENE[entrez_id], RO['0002200'], OMIM[mim_number]))
    hgnc_symbol_id_map: Dict[str, str] = get_hgnc_symbol_id_map()
    for mim_number, hgnc_symbol in hgnc_map.items():
        graph.add((OMIM[mim_number], SKOS.exactMatch, HGNC_symbol[hgnc_symbol]))
        if hgnc_symbol in hgnc_symbol_id_map:
            graph.add((OMIM[mim_number], SKOS.exactMatch, HGNC[hgnc_symbol_id_map[hgnc_symbol]]))

    # Phenotypic Series
    pheno_series = parse_phenotypic_series_titles(get_mim_file('phenotypicSeries.txt', download_files_tf))
    for ps_id in pheno_series:
        graph.add((OMIMPS[ps_id], RDF.type, OWL.Class))
        graph.add((OMIMPS[ps_id], RDFS.label, Literal(pheno_series[ps_id][0])))
        # Are all phenotypes listed here indeed disease? - joeflack4 2021/11/11
        graph.add((OMIMPS[ps_id], BIOLINK.category, BIOLINK.Disease))
        for mim_number in pheno_series[ps_id][1]:
            graph.add((OMIM[mim_number], RDFS.subClassOf, OMIMPS[ps_id]))

    # Morbid map
    morbid_map: Dict = parse_morbid_map(get_mim_file('morbidmap.txt', download_files_tf))
    for mim_number, mim_data in morbid_map.items():
        # todo?: unused `mim_data` keys. Should they be used?
        #  - phenotype_label: Similar to p_lab in 'assocs', but has more info
        #  - gene_symbols
        cyto_location: str = mim_data['cyto_location']
        if cyto_location:
            # What's 9606chr - joeflack4 2021/11/11
            chr_id = '9606chr' + cyto_location
            # RO:0002525 (is subsequence of)
            # https://www.ebi.ac.uk/ols/ontologies/ro/properties?iri=http://purl.obolibrary.org/obo/RO_0002525
            graph.add((OMIM[mim_number], RO['0002525'], CHR[chr_id]))
        assocs: List[Dict] = mim_data['phenotype_associations']
        for assoc in assocs:
            # p_lab currently not used
            p_mim, p_lab, p_map_key, p_map_lab = \
                assoc['phenotype_mim_number'], assoc['phenotype_label'], assoc['phenotype_mapping_info_key'], \
                assoc['phenotype_mapping_info_label']
            # Provenance: https://github.com/monarch-initiative/omim/issues/78
            if not p_mim:
                continue
            # Provenance: https://github.com/monarch-initiative/omim/issues/79#issuecomment-1319408780
            if p_map_key == '1':
                continue

            # Precalc: determine mapping predicate
            # RO:0003302 (causes or contributes to condition)
            # https://www.ebi.ac.uk/ols/ontologies/ro/properties?iri=http://purl.obolibrary.org/obo/RO_0003302
            # Provenance for this decision:
            # - Multiple rows, same mapping key: https://github.com/monarch-initiative/omim/issues/75
            # - Multiple rows, diff mapping keys: https://github.com/monarch-initiative/omim/issues/81
            predicate = RO['0003302']  # default if `len(assocs) > 1`
            if len(assocs) == 1:
                predicate = MORBIDMAP_PHENOTYPE_MAPPING_KEY_PREDICATES[p_map_key]

            # i. Add to MIM class
            b = BNode()
            graph.add((b, RDF['type'], OWL['Restriction']))
            graph.add((b, OWL['onProperty'], predicate))
            if p_mim:
                graph.add((b, OWL['someValuesFrom'], OMIM[p_mim]))
            graph.add((OMIM[mim_number], RDFS['subClassOf'], b))

            # ii. add axiom
            b2 = BNode()
            graph.add((b2, RDF['type'], OWL['Axiom']))
            graph.add((b2, OWL['annotatedSource'], OMIM[mim_number]))
            graph.add((b2, OWL['annotatedProperty'], RDFS['subClassOf']))
            # todo: add mapping key and related info in a different way?
            evidence = Literal(f'Evidence: ({p_map_key}) {p_map_lab}')
            # todo: add biolink:GeneDiseaseAssociation structure as well?
            graph.add((b2, BIOLINK['has_evidence'], evidence))
            graph.add((b2, RDFS['comment'], evidence))
            b3 = BNode()
            graph.add((b3, RDF['type'], OWL['Restriction']))
            graph.add((b3, OWL['onProperty'], predicate))
            if p_mim:
                graph.add((b3, OWL['someValuesFrom'], OMIM[p_mim]))
            graph.add((b2, OWL['annotatedTarget'], b3))

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

    with open(OUTPATH, 'w') as f:
        f.write(graph.serialize(format='turtle'))
    if issues:
        print(f'Warning: Issues detected. Check for details: {ISSUES_OUTPATH}', file=sys.stderr)
        with open(ISSUES_OUTPATH, 'w') as f:
            json.dump(issues, f, indent=2)
        # todo: report in TSV. remove when we are done looking over this issue
        #  - https://github.com/monarch-initiative/omim/issues/78
        rows = []
        for row in [
            x['morbidmap.txt_original_row'] for x in issues['morbid_map']['issue:nonNumericPhenotypeId'].values()]:
            new_row = {}
            new_row['Phenotype'], new_row['Gene Symbols'], new_row['MIM Number'], new_row['Cyto Location'] = \
                row.split('\t')
            rows.append(new_row)
        missing_mimnum_report = pd.DataFrame(rows)
        missing_mimnum_report.to_csv('~/Desktop/noMimNumsInPhenoLabels.tsv', sep='\t', index=False)


if __name__ == '__main__':
    omim2obo()

"""OMIM ingest to generate RDF .ttl

Resources
- https://monarch-initiative.github.io/monarch-ingest/Sources/OMIM/

FYIs
"Included Title(s)" in mimTitles.txt is the same as the "Other entities represented in this entry" section in omim.org
entry pages.

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
from omim2obo.parsers.omim_entry_parser import get_alt_and_included_titles_and_symbols, get_pubs, get_mapped_ids, \
    LabelCleaner
from omim2obo.config import ROOT_DIR, GLOBAL_TERMS
from omim2obo.parsers.omim_txt_parser import *


# Vars
OUTPATH = os.path.join(ROOT_DIR / 'omim.ttl')

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


def add_axiom_annotations(
    graph: Graph, source: URIRef, prop: URIRef, target: Union[Literal, str, URIRef],
    anno_pred_vals: List[Tuple[URIRef, Union[Literal, str, URIRef]]]
):
    """Add an axiom annotation to the graph."""
    target = Literal(target) if type(target) is str else target

    axiom = BNode()
    graph.add((axiom, RDF.type, OWL.Axiom))
    graph.add((axiom, OWL.annotatedSource, source))
    graph.add((axiom, OWL.annotatedProperty, prop))
    graph.add((axiom, OWL.annotatedTarget, target))
    for pred, val in anno_pred_vals:
        val = Literal(val) if type(target) is str else val
        graph.add((axiom, pred, val))


def add_triple_and_optional_annotations(
    graph: Graph, source: URIRef, prop: URIRef, target: Union[Literal, str, URIRef],
    anno_pred_vals: List[Tuple[URIRef, Union[Literal, str, URIRef]]] = None
):
    """Add a triple and optional annotations to the graph."""
    target = Literal(target) if type(target) is str else target

    graph.add((source, prop, target))
    if anno_pred_vals:
        add_axiom_annotations(graph, source, prop, target, anno_pred_vals)


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
    graph = OmimGraph.get_graph()
    download_files_tf: bool = not use_cache

    # Populate prefixes
    for prefix, uri in CURIE_MAP.items():
        graph.namespace_manager.bind(prefix, URIRef(uri))

    # Parse mimTitles.txt
    # - Get id's, titles, and type
    omim_type_and_titles, omim_replaced = parse_mim_titles(get_mim_file('mimTitles', download_files_tf))
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
        # Parse titles & symbols
        omim_type, pref_titles_str, alt_titles_str, inc_titles_str = omim_type_and_titles[omim_id]
        pref_titles_and_symbols: List[str] = [x.strip() for x in pref_titles_str.split(';')]
        pref_title, pref_symbols = pref_titles_and_symbols[0], pref_titles_and_symbols[1:]
        alt_titles, alt_symbols, former_alt_titles, former_alt_symbols = \
            get_alt_and_included_titles_and_symbols(alt_titles_str)
        included_titles, included_symbols, former_included_titles, former_included_symbols = \
            get_alt_and_included_titles_and_symbols(inc_titles_str)

        # Special cases depending on OMIM term type
        is_gene = omim_type == OmimType.GENE or omim_type == OmimType.HAS_AFFECTED_FEATURE
        if omim_type == OmimType.HERITABLE_PHENOTYPIC_MARKER:  # %
            graph.add((omim_uri, BIOLINK['category'], BIOLINK['Disease']))
        elif is_gene:  # * or +
            graph.add((omim_uri, RDFS.subClassOf, SO['0000704']))  # gene
            graph.add((omim_uri, MONDO.exclusionReason, MONDO.nonDisease))
            graph.add((omim_uri, BIOLINK['category'], BIOLINK['Gene']))
        elif omim_type == OmimType.PHENOTYPE:
            graph.add((omim_uri, BIOLINK['category'], BIOLINK['Disease']))  # phenotype ~= disease
        elif omim_type == OmimType.SUSPECTED:
            graph.add((omim_uri, MONDO.exclusionReason, MONDO.excludeTrait))

        # Alternative rdfs:label for genes
        if is_gene and pref_symbols:
            gene_label_err = 'Warning: Only 1 symbol picked for label for gene term, but there were 2 to choose' \
                 f'from. Unsure which is best. Picking the first.\nhttps://omim.org/entry/{omim_id} - {pref_symbols}'
            if len(pref_symbols) > 1:
                LOG.warning(gene_label_err)  # todo: rare (n=1?), but decide the best way to handle these situations
            graph.add((omim_uri, RDFS.label, Literal(pref_symbols[0])))
        else:
            graph.add((omim_uri, RDFS.label, Literal(label_cleaner.clean(pref_title))))

        # todo: .clean()/.cleanup_label() 2nd param `explicit_abbrev` should be List[str] instead of str. And below,
        #  should pass all symbols/abbrevs from each of preferred, alt, included each time it is called. If no symbols
        #  for given term, should pass empty list. See: https://github.com/monarch-initiative/omim/issues/129
        pref_abbrev: Union[str, None] = None if not pref_symbols else pref_symbols[0]

        # Add synonyms
        # - exact synonyms: titles
        graph.add((omim_uri, oboInOwl.hasExactSynonym, Literal(label_cleaner.clean(pref_title, pref_abbrev))))
        for title in alt_titles:
            graph.add((omim_uri, oboInOwl.hasExactSynonym, Literal(label_cleaner.clean(title, pref_abbrev))))
        # - exact synonyms: abbreviations
        for symbols in [pref_symbols, alt_symbols]:
            for symbol in symbols:
                add_triple_and_optional_annotations(graph, omim_uri, oboInOwl.hasExactSynonym, symbol,
                    [(oboInOwl.hasSynonymType, OMO['0003000'])])
        # - related, deprecated 'former' synonyms: titles
        for title in former_alt_titles:
            clean_title = label_cleaner.clean(title, pref_abbrev)
            add_triple_and_optional_annotations(graph, omim_uri, oboInOwl.hasExactSynonym, clean_title)
            add_triple_and_optional_annotations(graph, omim_uri, URIRef(MONDONS.omim_formerly), clean_title)
        # - related, deprecated 'former' synonyms: abbreviations
        for symbol in former_alt_symbols:
            add_triple_and_optional_annotations(graph, omim_uri, oboInOwl.hasExactSynonym, symbol,
                [(oboInOwl.hasSynonymType, OMO['0003000'])])
            # Though these are abbreviations, MONDONS.omim_formerly is not (yet) a synonym
            # type, so can't add axiom: (oboInOwl.hasSynonymType, OMO['0003000'])
            add_triple_and_optional_annotations(graph, omim_uri, URIRef(MONDONS.omim_formerly), symbol)

        # Add 'included' entries
        # - comment
        if included_titles:  # fyi: only need to check titles; there will never be included symbols w/out titles
            included_comment = "This term has one or more labels that end with ', INCLUDED'."
            graph.add((omim_uri, RDFS['comment'], Literal(included_comment)))
        # - titles
        for title in included_titles:
            graph.add((omim_uri, URIRef(MONDONS.omim_included), Literal(label_cleaner.clean(title, pref_abbrev))))
        # - symbols
        for symbol in included_symbols:
            add_triple_and_optional_annotations(graph, omim_uri, URIRef(MONDONS.omim_included), symbol, [
                # Though these are abbreviations, MONDONS.omim_included is not a synonym type, so can't add axiom:
                # (oboInOwl.hasSynonymType, OMO['0003000'])
            ])
        # - deprecated, 'former'
        for title in former_included_titles:
            clean_title = label_cleaner.clean(title, pref_abbrev)
            add_triple_and_optional_annotations(graph, omim_uri, URIRef(MONDONS.omim_included), clean_title)
            add_triple_and_optional_annotations(graph, omim_uri, URIRef(MONDONS.omim_formerly), clean_title)
        for symbol in former_included_symbols:
            # Though these are abbreviations, MONDONS.omim_included and MONDONS.omim_formerly is not (yet) a synonym
            # type, so can't add axiom: (oboInOwl.hasSynonymType, OMO['0003000'])
            add_triple_and_optional_annotations(graph, omim_uri, URIRef(MONDONS.omim_included), symbol)
            add_triple_and_optional_annotations(graph, omim_uri, URIRef(MONDONS.omim_formerly), symbol)


    # Gene ID
    # Why is 'skos:exactMatch' appropriate for disease::gene relationships? - joeflack4 2022/06/06
    get_mim_file('genemap2', download_files_tf)  # dl latest file
    mim2gene_lines: List[str] = get_mim_file('mim2gene', download_files_tf)  # dl latest file & return
    gene_map, pheno_map, hgnc_map = parse_mim2gene(mim2gene_lines)
    for mim_number, entrez_id in gene_map.items():
        graph.add((OMIM[mim_number], SKOS.exactMatch, NCBIGENE[entrez_id]))
    for mim_number, entrez_id in pheno_map.items():
        # RO['0002200'] = 'has phenotype'
        b = BNode()
        graph.add((b, RDF['type'], OWL['Restriction']))
        graph.add((b, OWL['onProperty'], RO['0002200']))
        graph.add((b, OWL['someValuesFrom'], OMIM[mim_number]))
        graph.add((NCBIGENE[entrez_id], RDFS['subClassOf'], b))
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
    morbid_map: Dict = parse_morbid_map(get_mim_file('morbidmap', download_files_tf))
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
            b = BNode()
            graph.add((b, RDF['type'], OWL['Restriction']))
            graph.add((b, OWL['onProperty'], RO['0002525']))
            graph.add((b, OWL['someValuesFrom'], CHR[chr_id]))
            graph.add((OMIM[mim_number], RDFS['subClassOf'], b))
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

            evidence = Literal(f'Evidence: ({p_map_key}) {p_map_lab}')
            
            # i. Add to MIM class
            # noinspection DuplicatedCode  b_and_b3_diff_results
            b = BNode()
            graph.add((b, RDF['type'], OWL['Restriction']))
            graph.add((b, OWL['onProperty'], predicate))
            graph.add((b, OWL['someValuesFrom'], OMIM[p_mim]))
            graph.add((OMIM[mim_number], RDFS['subClassOf'], b))

            # ii. add axiom
            b2 = BNode()
            graph.add((b2, RDF['type'], OWL['Axiom']))
            graph.add((b2, OWL['annotatedSource'], OMIM[mim_number]))
            graph.add((b2, OWL['annotatedProperty'], RDFS['subClassOf']))
            graph.add((b2, OWL['annotatedTarget'], b))
            graph.add((b2, BIOLINK['has_evidence'], evidence))
            graph.add((b2, RDFS['comment'], evidence))
            
            if predicate in MORBIDMAP_PHENOTYPE_MAPPING_KEY_INVERSE_PREDICATES:
                # The following code basically just adds the converse relation:
                # If there is g2d in the previous code, we now, in addition, add d2g
                inverse_predicate = MORBIDMAP_PHENOTYPE_MAPPING_KEY_INVERSE_PREDICATES[predicate]
               
                # i. Add to MIM class
                b = BNode()
                graph.add((b, RDF['type'], OWL['Restriction']))
                graph.add((b, OWL['onProperty'], inverse_predicate))
                graph.add((b, OWL['someValuesFrom'], OMIM[mim_number]))
                graph.add((OMIM[p_mim], RDFS['subClassOf'], b))
                
                b2 = BNode()
                graph.add((b2, RDF['type'], OWL['Axiom']))
                graph.add((b2, OWL['annotatedSource'], OMIM[p_mim]))
                graph.add((b2, OWL['annotatedProperty'], RDFS['subClassOf']))
                graph.add((b2, OWL['annotatedTarget'], b))
                graph.add((b2, BIOLINK['has_evidence'], evidence))
                graph.add((b2, RDFS['comment'], evidence))

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


if __name__ == '__main__':
    omim2obo()

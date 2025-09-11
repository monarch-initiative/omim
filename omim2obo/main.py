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
  - Add disease-gene associations
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
- Parses: hgnc/hgnc_complete_set.txt: mappings between  HGNC symbols and IDs. Get HGNC symbol::id mappings.

todo's
 - Downloads should all happen at beginning of script
 - This is last updated 4/2022 and now does not fully describe everything that happens.
 - Codestyle: Namespace prop access should be consistenly NAMESPACE.prop or NAMESPACE['prop'] (choose one)

Assumptions
1. Mappings obtained from official OMIM files as described above are interpreted correctly (e.g. skos:exactMatch).
"""
from typing import Optional

import yaml
from hashlib import md5

import os
import csv
from pathlib import Path
from collections import defaultdict
from os import makedirs


from rdflib import Graph, RDF, OWL, RDFS, Literal, BNode, URIRef, SKOS
from rdflib.term import Identifier

from omim2obo.config import REVIEW_CASES_PATH, ROOT_DIR, GLOBAL_TERMS
from omim2obo.namespaces import *
from omim2obo.parsers.omim_entry_parser import REVIEW_CASES, cleanup_title, get_alt_and_included_titles_and_symbols, \
    get_pubs, get_mapped_ids, log_review_cases, recapitalize_acronyms_in_titles
from omim2obo.parsers.omim_txt_parser import *  # todo: change to specific imports
from omim2obo.utils.utils import get_d2g_exclusions_by_curator, get_d2g_digenic_protections

# Vars
OUTPATH = os.path.join(ROOT_DIR / 'omim.ttl')

# Logging
LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)
LOG.addHandler(logging.StreamHandler(sys.stdout))


# Funcs
def load_omim_to_mondo_from_sssom(sssom_path: Path):
    """
    Build a map of OMIM to Mondo CURIEs from SSSOM file.
    """
    omim_to_mondo = defaultdict(set)
    if not sssom_path or not sssom_path.exists():
        LOG.warning(f"SSSOM file not found: {sssom_path} (will skip MONDO mapping)")
        return omim_to_mondo

    with sssom_path.open("r", newline="") as f:
        noncomment_lines = (line for line in f if line.strip() and not line.lstrip().startswith("#"))
        reader = csv.DictReader(noncomment_lines, delimiter="\t")

        for row in reader:
            sub = (row.get("subject_id") or "").strip()
            obj = (row.get("object_id") or "").strip()
            # Accept either orientation; normalize to OMIM -> MONDO
            if sub.startswith("OMIM:") and obj.startswith("MONDO:"):
                omim_to_mondo[sub.split(":", 1)[1]].add(obj)
            elif obj.startswith("OMIM:") and sub.startswith("MONDO:"):
                omim_to_mondo[obj.split(":", 1)[1]].add(sub)

    return omim_to_mondo


def get_curie_maps():
    """Retrieve CURIE to URL info"""
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


def add_subclassof_restriction(graph: Graph, predicate: URIRef, some_values_from: URIRef, on: URIRef) -> BNode:
    """Creates a subClassOf someValuesFrom restriction"""
    b = BNode()
    graph.add((b, RDF['type'], OWL['Restriction']))
    graph.add((b, OWL['onProperty'], predicate))
    graph.add((b, OWL['someValuesFrom'], some_values_from))
    graph.add((on, RDFS['subClassOf'], b))
    return b


def add_subclassof_restriction_with_evidence_and_source(
    graph: Graph, predicate: URIRef, some_values_from: URIRef, on: URIRef, evidence: Union[str, Literal],
    source: Optional[URIRef] = None,
):
    """Creates a subClassOf someValuesFrom restriction, and adds an evidence axiom to it."""
    evidence = Literal(evidence) if type(evidence) is str else evidence
    # Add restriction on MIM class
    b: BNode = add_subclassof_restriction(graph, predicate, some_values_from, on)
    # Add axiom to restriction
    annotation_pred_vals = [
        (BIOLINK['has_evidence'], evidence),
        (RDFS['comment'], evidence)
    ]
    annotation_pred_vals += [(oboInOwl.source, source)] if source else []

    add_axiom_annotations(graph, on, RDFS['subClassOf'], b, annotation_pred_vals)


# Classes
class DeterministicBNode(BNode):
    """Overrides BNode to create a deterministic ID"""

    def __new__(cls, source_ref: str):
        """Constructor
            source_ref: A reference to be passed to MD5 to generate _id.
        """
        _id: str = md5(source_ref.encode()).hexdigest()
        return Identifier.__new__(cls, _id)


def add_gene_disease_associations(graph: Graph, gene_mim: str, p_mim: str, evidence: str, orcid: str = None):
    """Add gene-disease associations in both directions."""
    # Add restrictions: Disease-defining ('causal germline mutation')
    # - Disease --(RO:0004003 'has material basis in germline mutation in')--> Gene
    #   https://www.ebi.ac.uk/ols4/ontologies/ro/properties?iri=http://purl.obolibrary.org/obo/RO_0004003
    add_subclassof_restriction_with_evidence_and_source(
        graph, RO['0004003'], OMIM[gene_mim], OMIM[p_mim], evidence, orcid)
    # - Gene --(RO:0004013 'is causal germline mutation in')--> Disease
    #   https://www.ebi.ac.uk/ols4/ontologies/ro/properties?iri=http://purl.obolibrary.org/obo/RO_0004013
    add_subclassof_restriction_with_evidence_and_source(
        graph, RO['0004013'], OMIM[p_mim], OMIM[gene_mim], evidence, orcid)


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
CONFIG = {
    'verbose': False
}


# Main
def omim2obo(use_cache: bool = False):
    """Run program"""
    graph = OmimGraph.get_graph()
    download_files_tf: bool = not use_cache

    mondo_omim_sssom_path = Path("mondo_exactmatch_omim.sssom.tsv")
    omim_to_mondo = load_omim_to_mondo_from_sssom(mondo_omim_sssom_path)
    susceptibility_rows = set()

    # Populate prefixes
    for prefix, uri in CURIE_MAP.items():
        graph.namespace_manager.bind(prefix, URIRef(uri))

    # Parse mimTitles.txt
    # - Get id's, titles, and type
    omim_type_and_titles, omim_replaced = parse_mim_titles(get_mim_file('mimTitles', download_files_tf))
    omim_types: Dict[str, str] = {k: v[0].name for k, v in omim_type_and_titles.items()}
    omim_ids = list(omim_type_and_titles.keys())

    if CONFIG['verbose']:
        print('Tot MIM numbers from mimTitles.txt: %i', len(omim_ids))
        print('Tot MIM types: %i', len(omim_type_and_titles))

    # Populate graph
    # - Non-OMIM triples
    ontology_iri = URIRef('http://purl.obolibrary.org/obo/mondo/omim.owl')
    # Add versionIRI with current date
    from datetime import datetime
    current_date = datetime.now().strftime('%Y-%m-%d')
    version_iri = URIRef(f'http://purl.obolibrary.org/obo/mondo/releases/{current_date}/omim.owl')
    version_info = URIRef(f'{current_date}')
    
    graph.add((ontology_iri, RDF.type, OWL.Ontology))
    graph.add((ontology_iri, OWL.versionIRI, version_iri))
    graph.add((ontology_iri, OWL.versionInfo, Literal(version_info)))
    graph.add((URIRef(oboInOwl.hasSynonymType), RDF.type, OWL.AnnotationProperty))
    graph.add((URIRef(oboInOwl.source), RDF.type, OWL.AnnotationProperty))
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
        pref_titles_and_symbols: List[str] = [x.strip() for x in pref_titles_str.split('; ')]
        pref_title, pref_symbols = cleanup_title(pref_titles_and_symbols[0]), pref_titles_and_symbols[1:]
        alt_titles, alt_symbols, former_alt_titles, former_alt_symbols = \
            get_alt_and_included_titles_and_symbols(alt_titles_str)
        included_titles, included_symbols, former_included_titles, former_included_symbols = \
            get_alt_and_included_titles_and_symbols(inc_titles_str)
        included_is_included = included_titles or included_symbols  # redundant. can't be included symbol w/out title

        # Recapitalize acronyms in titles
        all_abbrevs: Set[str] = \
            set(pref_symbols + alt_symbols + former_alt_symbols + included_symbols + former_included_symbols)
        # todo: consider DRYing to 1 call by passing all 5 title types to a wrapper function
        pref_title = recapitalize_acronyms_in_titles(pref_title, all_abbrevs)
        alt_titles = recapitalize_acronyms_in_titles(alt_titles, all_abbrevs)
        former_alt_titles = recapitalize_acronyms_in_titles(former_alt_titles, all_abbrevs)
        included_titles = recapitalize_acronyms_in_titles(included_titles, all_abbrevs)
        former_included_titles = recapitalize_acronyms_in_titles(former_included_titles, all_abbrevs)

        # Special cases depending on OMIM term type
        is_gene = omim_type == OmimType.GENE or omim_type == OmimType.HAS_AFFECTED_FEATURE
        if omim_type == OmimType.HERITABLE_PHENOTYPIC_MARKER:  # '%' char
            graph.add((omim_uri, BIOLINK['category'], BIOLINK['Disease']))
        elif is_gene:  # Represented by: * or + chars
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
                LOG.warning(gene_label_err)  # todo: rare (n=1?), but decide the best way to handle these situations
            graph.add((omim_uri, RDFS.label, Literal(pref_symbols[0])))
        else:
            graph.add((omim_uri, RDFS.label, Literal(pref_title)))

        # Add synonyms
        # - exact titles
        graph.add((omim_uri, oboInOwl.hasExactSynonym, Literal(pref_title)))
        for title in alt_titles:
            graph.add((omim_uri, oboInOwl.hasExactSynonym, Literal(title)))
        # - exact abbreviations
        for abbrevs in [pref_symbols, alt_symbols]:
            for abbreviation in abbrevs:
                add_triple_and_optional_annotations(graph, omim_uri, oboInOwl.hasExactSynonym, abbreviation,
                    [(oboInOwl.hasSynonymType, OMO['0003000'])])
        # - related, deprecated 'former' titles
        for title in former_alt_titles:
            add_triple_and_optional_annotations(graph, omim_uri, oboInOwl.hasRelatedSynonym, title,
                [(OWL.deprecated, Literal(True))])
        # - related, deprecated 'former' abbreviations
        for abbreviation in former_alt_symbols:
            add_triple_and_optional_annotations(graph, omim_uri, oboInOwl.hasRelatedSynonym, abbreviation,
                [(OWL.deprecated, Literal(True)), (oboInOwl.hasSynonymType, OMO['0003000'])])

        # Add 'included' entries
        # - comment
        if included_is_included:
            included_comment = "This term has one or more labels that end with ', INCLUDED'."
            graph.add((omim_uri, RDFS['comment'], Literal(included_comment)))
        # - titles
        for title in included_titles:
            graph.add((omim_uri, URIRef(MONDONS.omim_included), Literal(title)))
        # - symbols
        for symbol in included_symbols:
            add_triple_and_optional_annotations(graph, omim_uri, URIRef(MONDONS.omim_included), symbol, [
                # Though these are abbreviations, MONDONS.omim_included is not a synonym type, so can't add axiom:
                # (oboInOwl.hasSynonymType, OMO['0003000'])
            ])
        # - deprecated, 'former'
        for title in former_included_titles:
            add_triple_and_optional_annotations(graph, omim_uri, URIRef(MONDONS.omim_included), title,
                [(OWL.deprecated, Literal(True))])
        for symbol in former_included_symbols:
            add_triple_and_optional_annotations(graph, omim_uri, URIRef(MONDONS.omim_included), symbol, [
                (OWL.deprecated, Literal(True)),
                # Though these are abbreviations, MONDONS.omim_included is not a synonym type, so can't add axiom:
                # (oboInOwl.hasSynonymType, OMO['0003000'])
            ])

    # Gene ID
    # - Note that sometimes a gene symbol will appear on the omim.org/entry page, under the Phenotype-Gene or
    #   Gene-Phenotype tables, which will match its entry in morbidmap.txt. However, that does not guarantee that the
    #   gene will appear in mim2gene.txt. If it is not in mim2gene.txt, it will not be added.
    # - Why is 'skos:exactMatch' appropriate for disease::gene relationships? - joeflack4 2022/06/06
    # - genemap2: Is currently not used in the pipeline anywhere. It is downloaded simply for local reference.
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
    phenotype_genes: Dict[str, List[Dict[str, str]]] = get_phenotype_genes(gene_phenotypes)

    # - Add relations (subclass restrictions)
    exclusions_p_mim_orcid_map: Dict[str, Optional[URIRef]] = get_d2g_exclusions_by_curator()
    protections_gene_pheno__hgnc_orcid_map: Dict[Tuple[str, str], Tuple[str, Optional[URIRef]]] = \
        get_d2g_digenic_protections()
    for p_mim, assocs in phenotype_genes.items():
        for assoc in assocs:
            gene_mim, p_lab, p_map_key, p_map_lab = assoc['gene_id'], assoc['phenotype_label'], \
                assoc['mapping_key'], assoc['mapping_label']
            
            # Collect OMIM susceptibility entries (https://omim.org/help/faq#1_6)
            if p_lab and p_lab.strip().startswith("{"):
                # Map OMIM phenotype MIM -> MONDO IDs via SSSOM
                for mondo_id in sorted(omim_to_mondo.get(p_mim, [])):
                    susceptibility_rows.add((mondo_id, f"OMIM:{p_mim}"))

            evidence = f'Evidence: ({p_map_key}) {p_map_lab}'
            p_mim_excluded = p_mim in exclusions_p_mim_orcid_map
            protected_digenic_key = (p_mim, gene_mim)

            protected_digenic_assoc: bool = protected_digenic_key in protections_gene_pheno__hgnc_orcid_map
            if protected_digenic_assoc:
                hgnc_id_protected: str
                orcid_protected: Optional[URIRef]
                hgnc_id_protected, orcid_protected = protections_gene_pheno__hgnc_orcid_map[protected_digenic_key]
                add_gene_disease_associations(graph, gene_mim, p_mim, evidence, orcid_protected)
                graph.add((OMIM[gene_mim], SKOS.exactMatch, HGNC[hgnc_id_protected]))
                continue

            # Skip: No phenotype or unknown defect
            # - not p_mim: Skip because not an association to another MIM (Provenance:
            #  https://github.com/monarch-initiative/omim/issues/78)
            # - p_map_key == '1': Skip because association w/ unknown defect (Provenance:
            #  https://github.com/monarch-initiative/omim/issues/79#issuecomment-1319408780)
            if not p_mim or p_map_key == '1':
                continue

            # Add restrictions: Gene->Disease non-causal / non-disease-defining relationships
            # - RO:0003302 docs: see MORBIDMAP_PHENOTYPE_MAPPING_KEY_PREDICATES
            # - Mapping key 3 = 'causal' (disease-defining). Handled separately below.
            if p_map_key != '3' or p_mim_excluded:
                g2d_pred = MORBIDMAP_PHENOTYPE_MAPPING_KEY_PREDICATES[p_map_key] \
                    if len(assocs) == 1 and not p_mim_excluded \
                    else RO['0003302']
                orcid: Optional[URIRef] = exclusions_p_mim_orcid_map[p_mim] if p_mim_excluded else None
                add_subclassof_restriction_with_evidence_and_source(
                    graph, g2d_pred, OMIM[p_mim], OMIM[gene_mim], evidence, orcid)
                continue

            # Skip non-causal (disease-defining) cases
            if len(assocs) > 1 or not p2g_is_definitive(p_lab):  # or cases above: (p_map_key != '3') & p_mim_excluded
                continue

            log_review_cases(p_mim, p_lab, p_map_key, gene_mim, gene_phenotypes, omim_types)
            add_gene_disease_associations(graph, gene_mim, p_mim, evidence)

    # PubMed refs, UMLS mappings, Orphanet mappings
    pubmed_links_df, mappings_df = get_pubmed_refs_and_mappings()
    for df, field, pred, obj_ns in [
        (pubmed_links_df, 'pmid_refs', IAO['0000142'], PMID),
        (mappings_df, 'umls_ids', SKOS.exactMatch, UMLS),
        (mappings_df, 'orphanet_ids', SKOS.exactMatch, ORPHANET),
    ]:
        for _, row in df.iterrows():
            ids = str(row[field]).split('|') if row[field] else []
            for _id in ids:
                graph.add((OMIM[str(row['mim'])], pred, obj_ns[_id]))  # IAO:0000142: 'mentions'

    # Save ROBOT template for susceptibility annotations
    makedirs("robot_templates", exist_ok=True)
    susceptibility_out = Path("mondo-omim-susceptibility-subset.robot.tsv")
    with susceptibility_out.open("w", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["mondo_id", "subset", "omim_id"])
        w.writerow(["ID", "AI oboInOwl:inSubset", ">A oboInOwl:source"])
        for mondo_id, omim_curie in sorted(susceptibility_rows):
            w.writerow([mondo_id, "http://purl.obolibrary.org/obo/mondo#omim_susceptibility", omim_curie])

    # Save
    # - Review file
    # todo: ensure comment field exists even when no row uses it
    review_df = pd.DataFrame(REVIEW_CASES).sort_values(by=['classCode', 'value'])
    review_df.to_csv(REVIEW_CASES_PATH, index=False, sep='\t')
    # - Ontology
    with open(OUTPATH, 'w') as f:
        f.write(graph.serialize(format='turtle'))


if __name__ == '__main__':
    omim2obo()

"""Build for OMIM.ttl

Steps (Based on reading session 2021/11/11)

- Loads prefixes
- Parses mimTitles.txt
  - # - Get id's, titles, and type
  - add to graph
- parse mim2gene.txt
  - for mim_number, entrez_id in gene_map.items():
    - graph.add((OMIM[mim_number], OWL.equivalentClass, NCBIGENE[entrez_id]))
  - for mim_number, entrez_id in pheno_map.items():
    - graph.add((NCBIGENE[entrez_id], RO['0002200'], OMIM[mim_number]))
- parse phenotypicSeries.txt
  - Gets IDs and phenotype labels / descriptions
  - Gets mim numbers referenced
  - adds to graph
- parse morbidmap.txt
  - links omim entry (~gene) to phenotype
    - I thought phenotypic series did something like the sme?
  - links omim entry to chromosome location
- omim.ttl & updated_01_2020_to_08_2021.json
  - pmid info
  - umls info
  - orphanet info
  - add these to graph
- Add "omim replaced" info
  - This is gotten from mimTitles.txt at beginning
"""
# import json
import sys
# from rdflib import Graph, URIRef, RDF, OWL, RDFS, Literal, Namespace, DC, BNode
from hashlib import md5

import yaml
from rdflib import Graph, RDF, OWL, RDFS, Literal, BNode, URIRef
from rdflib.term import Identifier

from omim2obo.namespaces import *
from omim2obo.parsers.omim_entry_parser import cleanup_label, get_alt_labels, get_pubs, get_mapped_ids
# from omim2obo.omim_client import OmimClient
from omim2obo.config import ROOT_DIR, GLOBAL_TERMS
from omim2obo.parsers.omim_txt_parser import *
# from omim2obo.omim_code_scraper.omim_code_scraper import get_codes_by_yyyy_mm


# Logging
LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)
LOG.addHandler(logging.StreamHandler(sys.stdout))

# Vars
TAX_LABEL = 'Homo sapiens'
TAX_ID = GLOBAL_TERMS[TAX_LABEL]
TAX_URI = URIRef(TAX_ID)


# Funcs
def get_curie_maps():
    """Rectrieve CURIE to URL info"""
    map_file = DATA_DIR / 'dipper/curie_map.yaml'
    with open(map_file, "r") as f:
        maps = yaml.safe_load(f)
    return maps


CURIE_MAP = get_curie_maps()


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


def run(use_cache: bool = False):
    """Run program"""
    graph = OmimGraph.get_graph()
    download_files_tf: bool = not use_cache

    # Populate prefixes
    for prefix, uri in CURIE_MAP.items():
        graph.namespace_manager.bind(prefix, URIRef(uri))

    # Parse mimTitles.txt
    # - Get id's, titles, and type
    omim_titles, omim_replaced = parse_mim_titles(retrieve_mim_file('mimTitles.txt', download_files_tf))
    omim_ids = list(omim_titles.keys() - omim_replaced.keys())

    LOG.info('Have %i omim numbers from mimTitles.txt', len(omim_ids))
    LOG.info('Have %i total omim types ', len(omim_titles))

    # Populate graph
    graph.add((TAX_URI, RDF.type, OWL.Class))
    graph.add((TAX_URI, RDFS.label, Literal(TAX_LABEL)))
    for omim_id in omim_ids:
        omim_uri = OMIM[omim_id]
        graph.add((omim_uri, RDF.type, OWL.Class))
        omim_type, pref_label, alt_label, inc_label = omim_titles[omim_id]

        label = pref_label
        other_labels = []
        if alt_label:
            other_labels += get_alt_labels(alt_label)
        if inc_label:
            other_labels += get_alt_labels(inc_label)

        # Labels
        abbrev = label.split(';')[1].strip() if ';' in label else None

        if omim_type == OmimType.HERITABLE_PHENOTYPIC_MARKER:  # %
            graph.add((omim_uri, RDFS.label, Literal(cleanup_label(label))))
            graph.add((omim_uri, BIOLINK['category'], BIOLINK['Disease']))
        elif omim_type == OmimType.GENE or omim_type == OmimType.HAS_AFFECTED_FEATURE:  # * or +
            # omim_type = OmimType.GENE
            graph.add((omim_uri, RDFS.label, Literal(abbrev)))
            # What's SO['0000704'] - joeflack4 2021/11/11
            graph.add((omim_uri, RDFS.subClassOf, SO['0000704']))
            graph.add((omim_uri, BIOLINK['category'], BIOLINK['Gene']))
        elif omim_type == OmimType.PHENOTYPE:  # #
            graph.add((omim_uri, RDFS.label, Literal(cleanup_label(label))))
            graph.add((omim_uri, BIOLINK['category'], BIOLINK['Disease']))
        else:
            # All were 'OmimType.SUSPECTED' when I just checked. - joeflack4 2021/11/11
            graph.add((omim_uri, RDFS.label, Literal(cleanup_label(label))))

        exact_labels = [s.strip() for s in label.split(';')]
        if len(exact_labels) > 1:  # the last string is an abbreviation. Add OWL reification. See issue #2
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
            graph.add((omim_uri, oboInOwl.hasExactSynonym, Literal(cleanup_label(exact_label, abbrev))))

        for label in other_labels:
            graph.add((omim_uri, oboInOwl.hasRelatedSynonym, Literal(cleanup_label(label, abbrev))))

    # Gene ID
    gene_map, pheno_map = parse_mim2gene(retrieve_mim_file('mim2gene.txt', download_files_tf))
    for mim_number, entrez_id in gene_map.items():
        # Are they truly equivalent? - joeflack4 2021/11/11
        graph.add((OMIM[mim_number], OWL.equivalentClass, NCBIGENE[entrez_id]))
    for mim_number, entrez_id in pheno_map.items():
        # What's RO['0002200'] - joeflack4 2021/11/11
        graph.add((NCBIGENE[entrez_id], RO['0002200'], OMIM[mim_number]))

    # Phenotpyic Series
    pheno_series = parse_phenotypic_series_titles(retrieve_mim_file('phenotypicSeries.txt', download_files_tf))
    for ps_id in pheno_series:
        graph.add((OMIMPS[ps_id], RDF.type, OWL.Class))
        graph.add((OMIMPS[ps_id], RDFS.label, Literal(pheno_series[ps_id][0])))
        # Are all phenotypes listed here indeed disease? - joeflack4 2021/11/11
        graph.add((OMIMPS[ps_id], BIOLINK.category, BIOLINK.Disease))
        for mim_number in pheno_series[ps_id][1]:
            graph.add((OMIM[mim_number], RDFS.subClassOf, OMIMPS[ps_id]))

    # Morbid map (cyto locations)
    morbid_map: Dict[str, List[str]] = parse_morbid_map(retrieve_mim_file('morbidmap.txt', download_files_tf))
    for mim_number in morbid_map:
        phenotype_mim_number, cyto_location = morbid_map[mim_number]
        if phenotype_mim_number:
            # What's RO['0003303'] - joeflack4 2021/11/11
            graph.add((OMIM[mim_number], RO['0003303'], OMIM[phenotype_mim_number]))
        if cyto_location:
            # What's 9606chr - joeflack4 2021/11/11
            chr_id = '9606chr' + cyto_location
            # What's RO['0002525'] - joeflack4 2021/11/11
            graph.add((OMIM[mim_number], RO['0002525'], CHR[chr_id]))

    # PUBMED, UMLS
    # How do we get these w/out relying on this ttl file? Possible? Where is it from? - joeflack4 2021/11/11
    pmid_map, umls_map, orphanet_map = get_maps_from_turtle()

    # Get the recent updated
    # How long is this JSON file supposed to last for us Where is it from? - joeflack4 2021/11/11
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
            graph.add((OMIM[mim_number], oboInOwl.hasDbXref, UMLS[umls_id]))
    for mim_number, orphanet_ids in orphanet_map.items():
        for orphanet_id in orphanet_ids:
            graph.add((OMIM[mim_number], oboInOwl.hasDbXref, ORPHANET[orphanet_id]))

    # replaced
    # to-do: This makes more sense to me at the beginning, right after reading mimTitles.txt
    # ...since that's where thiscomes from. Try moving it up there, rerunning, and see
    # ...if get exact same results. -joeflack4 2021/11/11
    for mim_num, replaced in omim_replaced.items():
        if len(replaced) > 1:
            for replaced_mim_num in replaced:
                graph.add((OMIM[mim_num], oboInOwl.consider, OMIM[replaced_mim_num]))
        elif replaced:
            # What's IAO['0100001'] - joeflack4 2021/11/11
            graph.add((OMIM[mim_num], IAO['0100001'], OMIM[replaced[0]]))
        graph.add((OMIM[mim_num], RDF.type, OWL.Class))
        graph.add((OMIM[mim_num], OWL.deprecated, Literal(True)))

    with open(ROOT_DIR / 'omim.ttl', 'w') as f:
        f.write(graph.serialize(format='turtle'))
    # with open(ROOT_DIR / 'omim.xml', 'w') as f:
    #     f.write(graph.serialize(format='xml'))
    print("Job's done ;3")


if __name__ == '__main__':
    run()

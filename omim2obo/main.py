import json
import sys
from rdflib import Graph, URIRef, RDF, OWL, RDFS, Literal, Namespace, DC

from omim2obo.utils import cleanup_label
from omim2obo.omim_client import OmimClient
from omim2obo.config import config, DATA_DIR
from omim2obo.parsers.omim_txt_parser import *

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)
LOG.addHandler(logging.StreamHandler(sys.stdout))


def get_curie_maps():
    map_file = DATA_DIR / 'dipper/curie_map.yaml'
    with open(map_file, "r") as f:
        maps = yaml.safe_load(f)
    return maps


CURIE_MAP = get_curie_maps()


def build_uri(prefix, identifier):
    return URIRef(CURIE_MAP[prefix] + identifier)


class OmimGraph(Graph):
    __instance: Graph = None

    @staticmethod
    def get_graph():
        if OmimGraph.__instance is None:
            OmimGraph.__instance = Graph()
            for prefix, uri in CURIE_MAP.items():
                OmimGraph.__instance.namespace_manager.bind(prefix, URIRef(uri))
        return OmimGraph.__instance


if __name__ == '__main__':
    graph = OmimGraph.get_graph()
    for prefix, uri in CURIE_MAP.items():
        graph.namespace_manager.bind(prefix, URIRef(uri))

    # Parse mimTitles.txt
    omim_type, omim_replaced = parse_mim_titles(retrieve_mim_file('mimTitles.txt'))
    omim_genes = parse_mim_genes(retrieve_mim_file('mim2gene.txt'))
    omim_ids = list(omim_type.keys() - omim_replaced.keys())

    LOG.info('Have %i omim numbers from mimTitles.txt', len(omim_ids))
    LOG.info('Have %i total omim types ', len(omim_type))

    tax_label = 'Homo sapiens'
    tax_id = GLOBAL_TERMS[tax_label]

    tax_uri = URIRef(tax_id)
    graph.add((tax_uri, RDF.type, OWL.Class))
    graph.add((tax_uri, RDFS.label, Literal(tax_label)))

    for omim_id in omim_ids:
        omim_uri = build_uri('OMIM', omim_id)
        graph.add((omim_uri, RDF.type, OWL.Class))
        declared_type, pref_label, alt_label, inc_label = omim_type[omim_id]
        if omim_id in omim_genes:
            entry_type, entrez_id, gene_symbol, ensembl_id = omim_genes[omim_id]
            graph.add((omim_uri, RDFS.label, Literal(gene_symbol)))
            graph.add((omim_uri, DC.description, Literal(pref_label)))
        else:
            graph.add((omim_uri, RDFS.label, Literal(cleanup_label(pref_label))))
        if declared_type == OmimType.GENE:
            graph.add((omim_uri, RDFS.subClassOf, declared_type.value))
        graph.add((omim_uri, build_uri('oboInOwl', 'hasExactSynonym'), Literal(pref_label)))

    with open('output.ttl', 'wb') as f:
        f.write(graph.serialize(format='turtle'))

    # client = OmimClient(start=10000, total=5000, omim_ids=omim_ids, api_key=config['API_KEY'])
    # result = client.fetch_all()
    # with open('batch_3.json', 'w') as fout:
    #     json.dump(result, fout)







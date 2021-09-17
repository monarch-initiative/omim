"""OMIM Code PMID Query

Resources
- https://rdflib.readthedocs.io/en/stable/intro_to_sparql.html

TODO's
# to-do: 1. cache output
# TODO: Remove values like 'OMIM192240ref42' from end result
"""
import os
import pickle
from typing import List

from rdflib import Graph
from rdflib.query import Result
from rdflib.plugins.sparql import prepareQuery


GRAPH_FILENAME = 'omim.ttl'
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
graph_path = os.path.join(DATA_DIR, GRAPH_FILENAME)
pickle_path = os.path.join(DATA_DIR, 'cache', 'pickled', GRAPH_FILENAME + '.p')


# Working template; Returns data in the following form:
# (rdflib.term.URIRef('http://omim.org/entry/138140'),
# rdflib.term.URIRef('http://www.ncbi.nlm.nih.gov/pubmed/6328324'))
query_template = """
PREFIX IAO: <http://purl.obolibrary.org/obo/IAO_>
SELECT ?omim_code ?pmid
WHERE {
    ?omim_code IAO:0000142 ?pmid
}"""


def run(
    cache_results: bool = True,
    cached_graph_use: bool = True,
    cached_graph_new: bool = False
) -> List[str]:
    """Get list of "OMIM_CODE PMID" from omim.ttl

    Args:
        cache_results: Cache the query results?
        cached_graph_use: Use previously cached omim.ttl?
        cached_graph_new: Create new cache of omim.ttl?

    Returns:
        List[str]: In the form of ["OMIM_CODE PMID"]
    """
    # Load graph
    if cached_graph_use:
        try:
            graph = pickle.load(open(pickle_path, "rb"))
        except FileNotFoundError:
            print('Attempted to use cached file, but was not found.')
            cached_graph_use = False
    if not cached_graph_use:
        graph = Graph()
        graph.parse(graph_path)
        if cached_graph_new:
            pickle.dump(graph, open(pickle_path, "wb"))

    # Query
    query = prepareQuery(query_template)
    results: Result = graph.query(query)
    result_list: List[str] = []
    for result in results:
        from urllib.parse import urlparse
        # Option a: just using string functionality
        # e.g. omim_code.rsplit('/', 1)[-1]
        # Option b: urlparse
        omim_code = urlparse(str(result[0])).path.split('/')[-1]
        pmid = urlparse(str(result[1])).path.split('/')[-1]
        result_list.append(omim_code + ' ' + pmid)

    # Return
    if cache_results:
        pass  # to-do (1)
    return result_list


if __name__ == '__main__':
    from pprint import pprint
    pprint(run())

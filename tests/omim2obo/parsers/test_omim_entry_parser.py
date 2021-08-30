from omim2obo.main import CURIE_MAP
from omim2obo.parsers.omim_entry_parser import *
from omim2obo.config import ROOT, config
from omim2obo.namespaces import *
import json


def test_transform_entry_null():
    with open(ROOT / 'tests/files/entry_10500_NULL.json', 'r') as fin:
        entries = json.load(fin)
    entry = entries['omim']['entryList'][0]['entry']
    graph = transform_entry(entry)

    for prefix, uri in CURIE_MAP.items():
        graph.namespace_manager.bind(prefix, URIRef(uri))
    print(graph.serialize(format='turtle'))


def test_transform_entry_percent():
    with open(ROOT / 'tests/files/entry_100070_PERCENT.json', 'r') as fin:
        entries = json.load(fin)
    entry = entries['omim']['entryList'][0]['entry']
    graph = transform_entry(entry)

    for prefix, uri in CURIE_MAP.items():
        graph.namespace_manager.bind(prefix, URIRef(uri))
    print(graph.serialize(format='turtle'))


def test_transform_entry_asterisk_1():
    with open(ROOT / 'tests/files/entry_100660_ASTERISK.json', 'r') as fin:
        entries = json.load(fin)
    entry = entries['omim']['entryList'][0]['entry']
    graph = transform_entry(entry)

    for prefix, uri in CURIE_MAP.items():
        graph.namespace_manager.bind(prefix, URIRef(uri))

    omim_uri = OMIM[str(entry['mimNumber'])]
    assert (omim_uri, OWL.equivalentClass, NCBIGENE['218']) in graph
    print(graph.serialize(format='turtle'))


def test_transform_entry_asterisk_2():
    with open(ROOT / 'tests/files/entry_609300_ASTERISK.json', 'r') as fin:
        entries = json.load(fin)
    entry = entries['omim']['entryList'][0]['entry']
    graph = transform_entry(entry)

    for prefix, uri in CURIE_MAP.items():
        graph.namespace_manager.bind(prefix, URIRef(uri))

    omim_uri = OMIM[str(entry['mimNumber'])]
    print(graph.serialize(format='turtle'))


def test_transform_entry_plus():
    with open(ROOT / 'tests/files/entry_104250_PLUS.json', 'r') as fin:
        entries = json.load(fin)
    entry = entries['omim']['entryList'][0]['entry']
    graph = transform_entry(entry)

    for prefix, uri in CURIE_MAP.items():
        graph.namespace_manager.bind(prefix, URIRef(uri))
    print(graph.serialize(format='turtle'))


def test_transform_entry_number_sign():
    with open(ROOT / 'tests/files/entry_104500_NUMBER_SIGN.json', 'r') as fin:
        entries = json.load(fin)
    entry = entries['omim']['entryList'][0]['entry']
    graph = transform_entry(entry)

    for prefix, uri in CURIE_MAP.items():
        graph.namespace_manager.bind(prefix, URIRef(uri))

    omim_uri = OMIM[str(entry['mimNumber'])]
    assert (omim_uri, BIOLINK['category'], BIOLINK['Disease']) in graph
    print(graph.serialize(format='turtle'))

from omim2obo.parsers.omim_txt_parser import *
from omim2obo.config import ROOT, config


def test_parse_omim_id_1():
    omim_id = '123456'
    assert parse_omim_id(omim_id) == omim_id


def test_parse_omim_id_2():
    omim_id = '123456,'
    assert parse_omim_id(omim_id) == '123456'


def test_parse_omim_id_3():
    omim_id = '{123456}'
    assert parse_omim_id(omim_id) == '123456'


def test_parse_omim_id_4():
    omim_id = '{{123456}'
    assert parse_omim_id(omim_id) is None


def test_retrieve_mim_titles():
    config['API_KEY'] = 'INVALID_API_KEY'
    lines = retrieve_mim_titles()
    assert len(lines) > 20000


def test_parse_mim_titles():
    with open(ROOT / 'tests/files/mimTitles.txt', 'r') as fin:
        lines = fin.readlines()
    omim_type, omim_replaced = parse_mim_titles(lines)
    assert len(omim_type) == 27126
    assert len(omim_replaced) == 1316
    assert '100500' in omim_replaced
    assert omim_replaced['162820'] == ['147060', '150550', '252270']
    assert omim_type['100050'] == 'NCIT:C71458'



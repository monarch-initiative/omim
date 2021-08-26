import csv
from omim2obo.config import *
import logging
from omim2obo.config import config
import requests
import re
from typing import List, Dict, Tuple
from rdflib import URIRef
from collections import defaultdict

from omim2obo.omim_type import OmimType

LOG = logging.getLogger('omim2obo.parser.omim_titles_parser')


def retrieve_mim_file(file_name: str, download: bool = False):
    """
    Retrieve the mimTitles.txt file from the OMIM download server
    :return:
    """
    updated = False
    mim_file = DATA_DIR / file_name
    if download:
        url = f'https://data.omim.org/downloads/{config["API_KEY"]}/{file_name}'
        resp = requests.get(url)
        if resp.status_code == 200:
            text = resp.text
            if not text.startswith('<!DOCTYPE html>'):
                with open(mim_file, 'w') as fout:
                    fout.write(text)
                lines = text.split('\n')
                updated = True
                LOG.info('mimTitles.txt retrieved and updated')
        else:
            LOG.warning('Response from server: ' + resp.text)
    if not updated:
        # The server request failed. Use the cached file
        lines = []
        with open(mim_file, 'r') as fin:
            lines = fin.readlines()
        LOG.warning('Failed to retrieve mimTitles.txt. Using the cached file. ')
    return lines


def parse_mim_genes(lines):
    mim_genes = {}
    for line in lines:
        if line.startswith('#'):
            continue
        tokens = line.split('\t')
        if tokens[1] in ['moved/removed', 'phenotype', 'predominantly phenotypes']:
            continue
        if len(tokens) == 5:
            mim_number, entry_type, entrez_id, gene_symbol, ensembl_id = tokens
            mim_genes[mim_number] = (entry_type, entrez_id, gene_symbol, ensembl_id)
        else:
            LOG.warning("mim2gene - invalid line: ", line)
    return mim_genes


def parse_omim_id(omim_id):
    """
    Tries to fix an OMIM_ID
    :param omim_id:
    :return: If omim_id is in the correct format, return the id. Otherwise, return the fixed id.
    """
    if omim_id.isdigit() and len(omim_id) == 6:
        return omim_id
    else:
        LOG.warning(f'Trying to repaire malformed omim id: {omim_id}')
        m = re.match(r'\{(\d{6})\}', omim_id)
        if m:
            LOG.warning(f'Repaired malformed omim id: {m.group(1)}')
            return m.group(1)

        m = re.match(r'(\d{6}),', omim_id)
        if m:
            LOG.warning(f'Repaired malformed omim id: {m.group(1)}')
            return m.group(1)

        LOG.warning(f'Failed to repair malformed omim id: {omim_id}')
        return None


def parse_mim_titles(lines):
    """
    Parse the omim titles
    :param lines:
    :return: omim_type and omim_replaced, dicts that captures the type of the omim_id and if they've been replaced
    """
    omim_type = {}
    omim_replaced = {}
    declared_to_type = {
        'Caret': OmimType.OBSOLETE,  # 'HP:0031859',  # obsolete
        'Asterisk': OmimType.GENE,  # 'SO:0000704',  # gene
        'NULL': OmimType.SUSPECTED,  # 'NCIT:C71458',  # Suspected
        'Number Sign': OmimType.PHENOTYPE,  # 'UPHENO:0001001',  # phenotype
        'Percent': OmimType.HERITABLE_PHENOTYPIC_MARKER,  # 'SO:0001500',  # heritable_phenotypic_marker
        'Plus': OmimType.HAS_AFFECTED_FEATURE,  # 'GENO:0000418',  # has_affected_feature
    }
    for line in lines:
        if len(line) == 0 or line.isspace() or line[0] == '#':
            continue  # skip the comment lines
        declared, omim_id, pref_label, alt_label, inc_label = [i.strip() for i in line.split('\t')]
        if declared in declared_to_type:
            omim_type[omim_id] = (declared_to_type[declared], pref_label, alt_label, inc_label)
        else:
            LOG.error('Unknown OMIM type line %s', line)
        if declared == 'Caret':  # moved|removed|split -> moved twice
            omim_replaced[omim_id] = []
            if pref_label.startswith('MOVED TO '):
                replaced = [parse_omim_id(rep) for rep in pref_label[9:].split() if rep != 'AND']
                omim_replaced[omim_id] = list(filter(None, replaced))
    return omim_type, omim_replaced


def parse_phenotypic_series_titles(lines) -> Dict[str, List]:
    ret = defaultdict(list)
    for line in lines:
        if line.startswith('#'):
            continue
        tokens = line.split('\t')
        if len(tokens) == 2:
            ret[tokens[0].strip()].append(tokens[1].strip())
            ret[tokens[0].strip()].append([])
        if len(tokens) == 3:
            ret[tokens[0].strip()][1].append(tokens[1])
    return ret


def parse_gene_map(lines):
    ...


def parse_mim2gene(lines) -> Tuple:
    gene_map = {}
    pheno_map = {}
    for line in lines:
        if line.startswith('#'):
            continue
        tokens = line.split('\t')
        if tokens[1] == 'gene' or tokens[1] == 'gene/phenotype':
            if tokens[2]:
                gene_map[tokens[0]] = tokens[2]
        elif tokens[1] == 'phenotype' or tokens[1] == 'predominantly phenotypes':
            if tokens[2]:
                pheno_map[tokens[0]] = tokens[2]
    return gene_map, pheno_map


def parse_morbid_map(lines) -> Dict[str, List[str]]:
    ret = {}
    for line in lines:
        if line.startswith('#'):
            continue
        tokens = line.split('\t')
        penotype_omim_id = tokens[0].split(',')[-1].split(' ')[0]
        gene_omim_id = tokens[2]
        cyto_location = tokens[3]
        ret[gene_omim_id] = [penotype_omim_id, cyto_location]
    return ret


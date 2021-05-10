import csv
from omim2mondo.config import *
import logging
from omim2mondo.config import config
import requests
import re

from omim2mondo.omim_type import OmimType

LOG = logging.getLogger('omim2mondo.parser.omim_titles_parser')


def retrieve_mim_titles(download: bool = False):
    """
    Retrieve the mimTitles.txt file from the OMIM download server
    :return:
    """
    updated = False
    mim_titles_file = DATA_DIR / 'mimTitles.txt'
    if download:
        url = f'https://data.omim.org/downloads/{config["API_KEY"]}/mimTitles.txt'
        resp = requests.get(url)
        if resp.status_code == 200:
            text = resp.text
            if not text.startswith('<!DOCTYPE html>'):
                with open(mim_titles_file, 'w') as fout:
                    fout.write(text)
                lines = text.split('\n')
                updated = True
                LOG.info('mimTitles.txt retrieved and updated')
        else:
            LOG.warning('Response from server: ' + resp.text)
    if not updated:
        # The server request failed. Use the cached file
        lines = []
        with open(mim_titles_file, 'r') as fin:
            lines = fin.readlines()
        LOG.warning('Failed to retrieve mimTitles.txt. Using the cached file. ')
    return lines


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
            omim_type[omim_id] = declared_to_type[declared]
        else:
            LOG.error('Unknown OMIM type line %s', line)
        if declared == 'Caret':  # moved|removed|split -> moved twice
            omim_replaced[omim_id] = []
            if pref_label.startswith('MOVED TO '):
                replaced = [parse_omim_id(rep) for rep in pref_label[9:].split() if rep != 'AND']
                omim_replaced[omim_id] = list(filter(None, replaced))
    return omim_type, omim_replaced

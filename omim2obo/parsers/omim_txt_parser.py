"""Text parsing utilities"""
import logging
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import PosixPath
from typing import List, Dict, Set, Tuple, Union

import requests
import re
import pandas as pd

from omim2obo.config import CACHE_INCOMPLETENESS_INDICATOR_PATH, CACHE_LAST_UPDATED_PATH, CONFIG, DATA_DIR, \
    DISEASE_GENE_PROTECTED_PATH, HGNC_DATA_PATH, \
    MAPPINGS_PATH, \
    PUBMED_REFS_PATH
from omim2obo.namespaces import ORPHANET, RO, UMLS
from omim2obo.omim_client import OmimClient
from omim2obo.omim_type import OmimType
from omim2obo.parsers.omim_entry_parser import get_mapped_ids, get_pubs


LOG = logging.getLogger('omim2obo.parser.omim_titles_parser')
# MIM_NUMBER_DIGITS = 6  # if you see '6' in a regexp, this is what it refers to
# MORBIDMAP_PHENOTYPE_MAPPING_KEY_MEANINGS: The Monarch Ingest and Kevin S have identified some ECO properties that
# ...probably apply to each of these. See:
# https://github.com/monarch-initiative/monarch-ingest/blob/main/monarch_ingest/ingests/omim/omim-translation.yaml
# "1": "inference from background scientific knowledge used in manual assertion"
# "2": "genomic context evidence"
# "3": "sequencing assay evidence"
# "4": "sequencing assay evidence"
MORBIDMAP_PHENOTYPE_MAPPING_KEY_MEANINGS = {
    '1': 'The disorder is placed on the map based on its association with a gene, but the underlying defect is '
         'not known.',
    '2': 'The disorder has been placed on the map by linkage or other statistical method; no mutation has '
         'been found.',
    '3': 'The molecular basis for the disorder is known; a mutation has been found in the gene.',
    '4': 'A contiguous gene deletion or duplication syndrome, multiple genes are deleted or duplicated causing '
         'the phenotype.',
}
# todo: double check / handle edge cases if/as needed for any concerns:
#  - https://github.com/monarch-initiative/omim/issues/79#issuecomment-1319408780
# MORBIDMAP_PHENOTYPE_MAPPING_KEY_PREDICATES
# - Gene-to-Disease predicates
# - Provenance https://github.com/monarch-initiative/omim/issues/79#issuecomment-1319408780
MORBIDMAP_PHENOTYPE_MAPPING_KEY_PREDICATES = {
    '1': None,  # association with unknown defect
    # RO:0003303 (causes condition)
    # A relationship between an entity (e.g. a genotype, genetic variation, chemical, or environmental exposure) and a
    # condition (a phenotype or disease), where the entity has some causal role for the condition.
    # https://www.ebi.ac.uk/ols/ontologies/ro/properties?iri=http://purl.obolibrary.org/obo/RO_0003303
    '2': RO['0003303'],
    # RO:0004013 (is causal germline mutation in)
    # Relates a gene to condition, such that a mutation in this gene is sufficient to produce the condition and that
    # can be passed on to offspring[modified from orphanet].
    # https://www.ebi.ac.uk/ols/ontologies/ro/properties?iri=http://purl.obolibrary.org/obo/RO_0004013
    '3': RO['0004013'],
    # RO:0003304 (contributes to condition)
    # A relationship between an entity (e.g. a genotype, genetic variation, chemical, or environmental exposure) and a
    # condition (a phenotype or disease), where the entity has some contributing role that influences the condition.
    # https://www.ebi.ac.uk/ols/ontologies/ro/properties?iri=http://purl.obolibrary.org/obo/RO_0003304
    '4': RO['0003304'],
}

# RO:0003302 (causes or contributes to condition)
# - Note: This is used in main.py, but collecting documentation for it here.
# A relationship between an entity (e.g. a genotype, genetic variation, chemical, or environmental exposure)
# and a condition (a phenotype or disease), where the entity has some causal or contributing role that
# influences the condition.
# https://www.ebi.ac.uk/ols/ontologies/ro/properties?iri=http://purl.obolibrary.org/obo/RO_0003302
# Provenance for this decision:
# - Multiple rows, same mapping key: https://github.com/monarch-initiative/omim/issues/75
# - Multiple rows, diff mapping keys: https://github.com/monarch-initiative/omim/issues/81

# todo: these are unused variables. remove?:
# - Disease-to-Gene predicates
# RO:0004013 (is causal germline mutation in)
# https://www.ebi.ac.uk/ols/ontologies/ro/properties?iri=http://purl.obolibrary.org/obo/RO_0004013
#  is inverse of:
# RO:0004003 (has material basis in germline mutation in)
# https://www.ebi.ac.uk/ols4/ontologies/ro/properties?iri=http://purl.obolibrary.org/obo/RO_0004003
CAUSAL_GERMLINE_MUTATION_INVERSE_PREDICATES_G2D = {RO['0004013']: RO['0004003']}
CAUSAL_GERMLINE_MUTATION_INVERSE_PREDICATES_D2G = {RO['0004003']: RO['0004013']}


def convert_txt_to_tsv(file_name: str):
    """Convert OMIM text file to TSV, saving the TSV.

    todo: Preserve comments at top and bottom. There's a func that does this somewhere for the ones at top.
    todo: If we refactor codebase to use pandas instead of lines, consider:
      - This converts 'NULL' to `nan`. Is this what we want?
    """
    file_name = file_name if file_name.endswith('.txt') else file_name + '.txt'
    mim_file_path: PosixPath = DATA_DIR / file_name
    mim_file_tsv_path: str = str(mim_file_path).replace('.txt', '.tsv')
    with open(mim_file_path, 'r') as file:
        lines = file.readlines()

    # Find the header (last comment line at the top) and start of data
    header = None
    data_start = 0
    for i, line in enumerate(lines):
        if line.startswith('#'):
            header = line.strip('#').strip().split('\t')
            data_start = i + 1
        else:
            break

    # Find the end of data (first comment line from the bottom)
    data_end = len(lines)
    for i in range(len(lines) - 1, data_start - 1, -1):
        if lines[i].startswith('#'):
            data_end = i
        else:
            break

    # Create DataFrame
    data = [line.strip().split('\t') for line in lines[data_start:data_end]]
    df = pd.DataFrame(data, columns=header)
    df.to_csv(mim_file_tsv_path, sep='\t', index=False)


def update_mim_file_with_protected(
    file_name: str, inpath: str, outpath: str, protected_path=DISEASE_GENE_PROTECTED_PATH
):
    """Update the files downloaded from OMIM to add information we've set in protected-disease-gene.tsv

    Information about this 'protected' file can be found in the docs (README.md).

    mim2gene.txt: As of 2025/03/05, it turned out there were no missing rows in this file. So this code is here now more
    for futureproofing purposes.

    todo: Consider handling situation where protection file is intended only to protect a phenotype without stipulation
     of gene. That is, if the gene column is empty, skip to avoid error here: gene_mim = row['gene_mim'].split(':')[1]
    """
    outpath_with_header = outpath.replace('.tsv', '-with-header.tsv')
    df = pd.read_csv(inpath, comment='#', sep='\t', dtype=str).fillna('')
    df['is_added_protection'] = False
    prot_df = pd.read_csv(protected_path, sep='\t').fillna('')
    hgnc_id_symbols: Dict[str, str] = get_hgnc_id_symbol_map()

    if file_name == 'morbidmap.txt':
        new_prot_rows = []
        for _index, row in prot_df.iterrows():
            phenotype_mim = row['phenotype_mim'].split(':')[1]
            gene_mim = row['gene_mim'].split(':')[1]
            symbol = hgnc_id_symbols[row['hgnc_id']]
            # Disallow dupes
            gene_phenos = parse_morbid_map(read_mim_file_as_lines(inpath.replace('.tsv', '.txt')))
            pheno_genes = get_phenotype_genes(gene_phenos)
            pheno_genes_flatter = [[
                (p_mim, assoc['mapping_key'], assoc['gene_id']) for assoc in assocs]
                for p_mim, assocs in pheno_genes.items()]
            # - existing_records: Set[Tuple[pheno_mim, mapping_key, gene_mim]]
            existing_records: Set[Tuple[str, str, str]] = set([x for sublist in pheno_genes_flatter for x in sublist])
            if (phenotype_mim, '3', gene_mim) in existing_records:  # mapping_key 3 = disease defining
                continue
            # Construct phenotype field
            labels_df = pd.read_csv(DATA_DIR / 'mimTitles.tsv', sep='\t', comment='#')
            mim_label_map: Dict[str, str] = dict(
                zip(labels_df['MIM Number'].astype(str), labels_df['Preferred Title; symbol']))
            phenotype_label = mim_label_map[phenotype_mim].capitalize()  # not perfect case, but fine for our purposes
            phenotype_field = f'{phenotype_label}, {phenotype_mim} (3)'
            new_prot_rows.append({
                'Phenotype': phenotype_field,
                'Gene/Locus And Other Related Symbols': symbol,  # not comprehensive or strictly needed for our purposes
                'MIM Number': gene_mim,
                'Cyto Location': '',  # don't have this information; not needed for our purposes
                'is_added_protection': True,
            })
        df = pd.concat([df, pd.DataFrame(new_prot_rows)], ignore_index=True)
    elif file_name == 'mim2gene.txt':
        existing_records: Set[Tuple[str, str]] = set(
            zip(df['MIM Number'].astype(str), df['Approved Gene Symbol (HGNC)']))
        new_prot_rows = []
        for _index, row in prot_df.iterrows():
            gene_mim = row['gene_mim'].split(':')[1]
            symbol = hgnc_id_symbols[row['hgnc_id']]
            if (gene_mim, symbol) in existing_records:
                continue
            new_prot_rows.append({
                'MIM Number': gene_mim,
                # Not sure if 'gene/phenotype' is more technically correct, but for our pruposes, shouldn't matter.
                'MIM Entry Type (see FAQ 1.3 at https://omim.org/help/faq)': 'gene',
                'Entrez Gene ID (NCBI)': '',  # don't have this information; not needed for our purposes
                'Approved Gene Symbol (HGNC)': symbol,
                'Ensembl Gene ID (Ensembl)': '',  # don't have this information; not needed for our purposes
                'is_added_protection': True,
            })
        df = pd.concat([df, pd.DataFrame(new_prot_rows)], ignore_index=True)
    else:
        return  # no alterations needed for this file type

    df = df.astype(str)
    df.drop(columns=['is_added_protection']).to_csv(outpath, sep='\t', index=False, header=False)
    df.to_csv(outpath_with_header, sep='\t', index=False)


def read_mim_file_as_lines(path) -> List[str]:
    """Read MIM file as list of field values, rather than a dataframe."""
    with open(path, 'r') as fin:
        lines: List[str] = fin.readlines()
        # Remove # comments
        # - OMIM files always have comments at the top, and sometimes also at the bottom.
        lines = [x for x in lines if not x.startswith('#')]
        return lines


def get_mim_file(
    file_name: str, download=False, return_df=False, include_protected=True
) -> Union[List[str], pd.DataFrame]:
    """Retrieve OMIM downloadable text file from the OMIM download server

    :param return_df: If False, returns List[str] of each line in the file, else a DataFrame.
    :param include_protected: Only matters if file_name is in files_to_include_protected.
    """
    files_to_include_protected = ('morbidmap.txt', 'mim2gene.txt')
    file_name = file_name if file_name.endswith('.txt') else file_name + '.txt'
    mim_file_path: PosixPath = DATA_DIR / file_name
    mim_file_tsv_path: str = str(mim_file_path).replace('.txt', '.tsv')
    protected_added_path: str = mim_file_tsv_path.replace('.tsv', '-protected-added.tsv')

    if download:
        print(f'Downloading {file_name} from OMIM...')
        url = f'https://data.omim.org/downloads/{CONFIG["API_KEY"]}/{file_name}'
        # todo: This doesn't work for genemap2.txt. But does the previous URL work? If so, why not just use that?
        if file_name == 'mim2gene.txt':
            url = f'https://omim.org/static/omim/data/{file_name}'
        resp = requests.get(url)
        if resp.status_code == 200:
            text = resp.text
            if not text.startswith('<!DOCTYPE html>'):
                # Save
                with open(mim_file_path, 'w') as fout:
                    fout.write(text)
                convert_txt_to_tsv(file_name)
            else:
                raise RuntimeError('Unexpected response: ' + text)
        else:
            msg = 'Response from server: ' + resp.text
            # LOG.warning(msg)
            # with open(mim_file, 'r') as fin:
            #     lines = fin.readlines()
            # LOG.warning('Failed to retrieve mimTitles.txt. Using the cached file.')
            raise RuntimeError(msg)

    # Update w/ protected entries
    if file_name in files_to_include_protected:
        update_mim_file_with_protected(file_name, mim_file_tsv_path, protected_added_path)
    use_protected_file = include_protected and file_name in files_to_include_protected and \
        os.path.exists(protected_added_path)

    if return_df:
        read_path: str = protected_added_path if use_protected_file else mim_file_tsv_path
        return pd.read_csv(read_path, comment='#', sep='\t')
    else:
        read_path: str = protected_added_path if use_protected_file else mim_file_path
        return read_mim_file_as_lines(read_path)


def parse_mim_genes(lines):
    """Parse mim2gene.txt"""
    mim_genes = {}
    for line in lines:
        if line.startswith('#'):
            continue
        tokens = line.split('\t')
        if not tokens or tokens == ['']:
            continue
        if tokens[1] in ['moved/removed', 'phenotype', 'predominantly phenotypes']:
            continue
        if len(tokens) == 5:
            mim_number, entry_type, entrez_id, gene_symbol, ensembl_id = tokens
            mim_genes[mim_number] = (entry_type, entrez_id, gene_symbol, ensembl_id)
        else:
            LOG.warning("mim2gene - invalid line: ", line)
    return mim_genes


def parse_omim_id(omim_id, log_success_case_warnings=False):
    """
    Tries to fix an OMIM_ID
    :param omim_id:
    :return: If omim_id is in the correct format, return the id. Otherwise, return the fixed id.
    """
    if omim_id.isdigit() and len(omim_id) == 6:
        return omim_id
    else:
        if log_success_case_warnings:
            LOG.warning(f'Trying to repair malformed omim id: {omim_id}')
        # 6 = MIM_NUMBER_DIGITS
        # RegExpRedundantEscape: I'm not sure it's redundant, though it could be
        # noinspection RegExpRedundantEscape
        m = re.match(r'\{(\d{6})\}', omim_id)
        if m:
            if log_success_case_warnings:
                LOG.warning(f'Repaired malformed omim id: {m.group(1)}')
            return m.group(1)

        m = re.match(r'(\d{6}),', omim_id)
        if m:
            if log_success_case_warnings:
                LOG.warning(f'Repaired malformed omim id: {m.group(1)}')
            return m.group(1)

        LOG.warning(f'Failed to repair malformed omim id: {omim_id}')
        return None


def parse_mim_titles(lines) -> Tuple[Dict[str, Tuple[OmimType, str, str, str]], Dict[str, List[str]]]:
    """
    Parse the omim titles
    :param lines:
    :return:
      omim_type_and_titles: Dict[str, Tuple[OmimType, str, str, str]]: Lookup of MIM's type, as well as it's preferred
      labels, alternative labels, and 'included' labels.
      omim_replaced: Dict[str, List[str]]: Lookup of obsolete MIMs and a list of any different MIMs that it has been
       replaced with / moved to.
    """
    omim_type_and_titles = {}
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
        if not declared and not omim_id and not pref_label and not alt_label and not inc_label:
            continue
        if declared in declared_to_type:
            omim_type_and_titles[omim_id] = (declared_to_type[declared], pref_label, alt_label, inc_label)
        else:
            LOG.error('Unknown OMIM type line %s', line)
        if declared == 'Caret':  # moved|removed|split -> moved twice
            omim_replaced[omim_id] = []
            if pref_label.startswith('MOVED TO '):
                replaced = [parse_omim_id(rep) for rep in pref_label[9:].split() if rep != 'AND']
                omim_replaced[omim_id] = list(filter(None, replaced))
    return omim_type_and_titles, omim_replaced


def parse_phenotypic_series_titles(lines) -> Dict[str, List]:
    """Parse phenotypic series titles"""
    ret = defaultdict(list)
    for line in lines:
        if line.startswith('#'):
            continue
        tokens = line.split('\t')
        if not tokens or tokens == ['']:
            continue
        ps_id = tokens[0].strip()[2:]
        if len(tokens) == 2:
            ret[ps_id].append(tokens[1].strip())
            ret[ps_id].append([])
        if len(tokens) == 3:
            ret[ps_id][1].append(tokens[1])
    return ret


def parse_gene_map(lines):
    """To be implemented"""
    print(lines)
    ...


def get_hgnc_map(filename, symbol_col, mim_col='MIM Number') -> Dict:
    """Get HGNC Map"""
    d = {}
    input_path = DATA_DIR / filename
    try:
        df = pd.read_csv(input_path, delimiter='\t', comment='#').fillna('')
        df[mim_col] = df[mim_col].astype(int)  # these were being read as floats
    # TODO: Need a better solution than this. Which should be: When these files are downloaded, should uncomment header
    except KeyError:
        with open(input_path, 'r') as f:
            lines = f.readlines()
            header = lines[3]
            if not header.startswith('# Chromosome'):
                raise RuntimeError(f'Error parsing header for: {input_path}')
            lines[3] = header[2:]
        with open(input_path, 'w') as f:
            f.writelines(lines)
    finally:
        df = pd.read_csv(input_path, delimiter='\t', comment='#').fillna('')
        df[mim_col] = df[mim_col].astype(int)  # these were being read as floats

    for index, row in df.iterrows():
        symbol = row[symbol_col]
        if symbol:
            # Useful to read as `int` to catch any erroneous entries, but convert to str for compatibility with rest of
            # codebase, which is currently reading as `str` for now.
            d[str(row[mim_col])] = symbol

    return d


def parse_mim2gene(lines: List[str], filename='mim2gene.tsv', filename2='genemap2.tsv') -> Tuple[Dict, Dict, Dict]:
    """Parse OMIM # 2 gene file
    todo: ideally replace this whole thing with pandas
    todo: How to reconcile inconsistent mim#::hgnc_symbol mappings?
    todo: Generate inconsistent mapping report as csv output instead and print a single warning with path to that file.
    """
    # Gene and phenotype maps
    gene_map = {}
    pheno_map = {}
    for line in lines:
        if line.startswith('#'):
            continue
        tokens = line.split('\t')
        if not tokens or tokens == ['']:
            continue
        if tokens[1] == 'gene' or tokens[1] == 'gene/phenotype':
            if tokens[2]:
                gene_map[tokens[0]] = tokens[2]
        elif tokens[1] == 'phenotype' or tokens[1] == 'predominantly phenotypes':
            if tokens[2]:
                pheno_map[tokens[0]] = tokens[2]

    # HGNC map
    hgnc_map: Dict = get_hgnc_map(os.path.join(DATA_DIR, filename), 'Approved Gene Symbol (HGNC)')
    hgnc_map2: Dict = get_hgnc_map(os.path.join(DATA_DIR, filename2), 'Approved Gene Symbol')
    warning = 'Warning: MIM # {} was mapped to two different HGNC symbols, {} and {}. ' \
              'This was unexpected, so this mapping has been removed.'
    for mim_num, symbol in hgnc_map2.items():
        if mim_num not in hgnc_map:
            hgnc_map[mim_num] = symbol
        elif hgnc_map[mim_num] != symbol:
            LOG.warning(warning.format(mim_num, hgnc_map[mim_num], symbol))
            del hgnc_map[mim_num]

    return gene_map, pheno_map, hgnc_map


def parse_morbid_map(lines) -> Dict[str, Dict]:
    """Parse morbid map file. Part of this inspired by:
    https://github.com/monarch-initiative/monarch-ingest/blob/main/monarch_ingest/ingests/omim/gene_to_disease.py

    # todo: consider not adding to `d` if no phenotype_mim_number present, since we're skipping in `main.py`
    """
    # phenotype_label_regex: groups: (1) phenotype label, (2) MIM number (optional),
    # (3) phenotype mapping key (optional)
    phenotype_label_regex = re.compile(r'(.*)(\d{6})\s*(?:\((\d+)\))?')
    # phenotype_label_regex: groups: (1) phenotype label, (2) phenotype mapping key (optional)
    phenotype_label_no_mim_regex = re.compile(r'(.*)\s+\((\d+)\)')

    # Aggregate data by gene MIM
    gene_phenotypes: Dict[str, Dict] = {}
    for line in lines:
        if line.startswith('#'):
            continue
        fields: List[str] = line.split('\t')
        if not fields or fields == ['']:
            continue

        phenotype_label_and_metadata: str = fields[0]
        gene_symbols: List[str] = fields[1].split(', ')
        mim_number: str = fields[2].strip()  # todo: eventually would like this to be `int`
        cyto_location: str = fields[3].strip()

        phenotype_label, phenotype_mim_number, association_key = '', '', ''
        label_data_with_mim_num = phenotype_label_regex.match(phenotype_label_and_metadata)
        label_data_no_mim_num = phenotype_label_no_mim_regex.match(phenotype_label_and_metadata)

        if label_data_with_mim_num:
            phenotype_label, phenotype_mim_number, association_key = label_data_with_mim_num.groups()
        elif label_data_no_mim_num:
            phenotype_label, association_key = label_data_no_mim_num.groups()
        else:
            print(f'Warning: Failed to parse phenotype label in morbidmap.txt row: {line}', file=sys.stderr)

        if mim_number not in gene_phenotypes:
            gene_phenotypes[mim_number] = {
                'gene_mim_number': mim_number,
                'cyto_location': cyto_location,
                'gene_symbols': gene_symbols,
                'phenotype_associations': []
            }
        # todo: gene_mim_number in gene_mim_data:, print warning / raise err if gene_mim_number, cyto_location, or
        #  gene_symbols are != what's already there, but it shouldn't happen if morbidmap.txt is valid, I think.
        # noinspection PyTypeChecker
        gene_phenotypes[mim_number]['phenotype_associations'].append({
            'phenotype_mim_number': phenotype_mim_number,
            'phenotype_label': phenotype_label,
            'phenotype_mapping_info_key': association_key,
            'phenotype_mapping_info_label': MORBIDMAP_PHENOTYPE_MAPPING_KEY_MEANINGS[association_key],
        })

    return gene_phenotypes


def get_all_phenotype_mims() -> Set[str]:
    """Get all phenotype MIM numbers"""
    p_mims = []
    gene_phenotypes: Dict[str, Dict] = parse_morbid_map(get_mim_file('morbidmap'))
    for gene, d in gene_phenotypes.items():
        for assoc in d['phenotype_associations']:
            p_mims.append(assoc['phenotype_mim_number'])
    p_mims = set(p_mims)
    p_mims.discard('')
    return p_mims


def _read_cached_entry_df(path: str) -> pd.DataFrame:
    """Read a dataframe containing MIM entries data cached from the OMIM API"""
    return pd.read_csv(path, sep='\t', true_values=['True'], false_values=['False'], dtype={
        'is_phenotype': bool, 'mim': str, 'umls_ids': str, 'orphanet_ids': str, 'date_fetched': str})


def update_cache__pubmed_refs_and_mappings(phenotypes_only_for_cache_init=False, overwrite=False):
    """Update cache for MIM entries (pubmed refs & mappings) if cache is not complete or there is possibly new data"""
    # Load existing data
    mims_phenos: Set[str] = get_all_phenotype_mims()
    mappings_df_cached = _read_cached_entry_df(MAPPINGS_PATH) if os.path.exists(MAPPINGS_PATH) and not overwrite \
        else pd.DataFrame()
    pubmed_df_cached = _read_cached_entry_df(PUBMED_REFS_PATH) if os.path.exists(PUBMED_REFS_PATH) and not overwrite \
        else pd.DataFrame()

    # Fetch
    client = OmimClient(api_key=CONFIG['API_KEY'])
    # - Fetch everything if no cache or cache incomplete
    if not os.path.exists(CACHE_LAST_UPDATED_PATH) or os.path.exists(CACHE_INCOMPLETENESS_INDICATOR_PATH):
        print('Cache for pubmed references and mappings is incomplete.')
        # Determine MIMs to fetch
        # - Get all MIMs
        if phenotypes_only_for_cache_init:
            mims_all = mims_phenos
        else:
            df = get_mim_file('mimTitles', return_df=True)
            df['MIM Number'] = df['MIM Number'].astype(str)
            mims_all = set(df['MIM Number'])
        mims_all.discard('')
        # - Get cached MIMs
        mims_cached: Set[str] = set(mappings_df_cached['mim']) if len(mappings_df_cached) > 0 else set()
        mims_cached |= set(pubmed_df_cached['mim']) if len(pubmed_df_cached) > 0 else set()
        # Fetch
        results: List[Dict] = client.fetch(ids=list(mims_all - mims_cached), update_cache_metadata=True, seed_run=True)
    # - Else fetch new data if available
    else:
        print('Checking for recently updated MIMs.')
        # Applies precaution: -1 day from last fetched: to account for MIMs updated later in the day
        with open(CACHE_LAST_UPDATED_PATH, 'r') as f:
            last_updated_str = f.readline().strip()
        last_updated: datetime = datetime.strptime(last_updated_str, "%Y-%m-%d")
        last_updated = last_updated - timedelta(days=1)
        results: List[Dict] = client.fetch(since_date=last_updated, update_cache_metadata=True)

    # Save
    if len(results) == 0:
        return
    # - Create dataframes from fetched data
    mappings_rows: List[Dict] = []
    pubmed_rows: List[Dict] = []
    for entry in results:
        mim = str(entry['mimNumber'])
        mappings = get_mapped_ids(entry)
        common_data = {
            'mim': str(mim),
            'is_phenotype': str(mim) in mims_phenos,
            'date_fetched': datetime.now().strftime("%Y-%m-%d"),
        }
        mappings_rows.append({**common_data, **{
            'umls_ids': '|'.join(mappings[UMLS]),
            'orphanet_ids': '|'.join(mappings[ORPHANET]),
        }})
        pubmed_rows.append({**common_data, **{
            'pmid_refs': '|'.join(get_pubs(entry)),
        }})
    mappings_df_new = pd.DataFrame(mappings_rows)
    pubmed_df_new = pd.DataFrame(pubmed_rows)
    # Update cache & save
    # - remove old data from cache if new data has been fetched
    mappings_df_cached_del_old = mappings_df_cached[~mappings_df_cached['mim'].isin(mappings_df_new['mim'])]
    pubmed_df_cached_del_old = pubmed_df_cached[~pubmed_df_cached['mim'].isin(pubmed_df_new['mim'])]
    # - concat & save
    mappings_df = pd.concat([mappings_df_cached_del_old, mappings_df_new], ignore_index=True).sort_values(['mim'])
    pubmed_df = pd.concat([pubmed_df_cached_del_old, pubmed_df_new], ignore_index=True).sort_values(['mim'])
    mappings_df.to_csv(MAPPINGS_PATH, sep='\t', index=False)
    pubmed_df.to_csv(PUBMED_REFS_PATH, sep='\t', index=False)


def get_pubmed_refs_and_mappings(
    pubmed_path=PUBMED_REFS_PATH, mappings_path=MAPPINGS_PATH
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Get pubmed references &* mappings for MIMs*

    * Mondo only needs phenotypes, so not all MIMs are represented in cached data. Cached data was first updated in
    2025/03. At this time, only phenotype MIM information was saved. However, OMIM releases information about what MIMs
    were updated monthly, and this is used to update the cache. That information does not discriminate between phenotype
    and non-phenotype, so the cache will include any non-MIMs that were updated after 2025/03.

    todo: Would be more optimal to load these using dtypes than str cast later
    """
    update_cache__pubmed_refs_and_mappings()
    return pd.read_csv(pubmed_path, sep='\t').fillna(''), pd.read_csv(mappings_path, sep='\t').fillna('')


# todo: Both HGNC funcs:
#  1. Address or suppress warning. I dont even need these columns anyway:
#   ...omim2obo/main.py:208: DtypeWarning: Columns (32,34,38,40,50) have mixed types.
#   Specify dtype option on import or set low_memory=False.
#   hgnc_symbol_id_map: Dict = get_hgnc_symbol_id_map()
#  2. todo: Ideally download latest file: http://ftp.ebi.ac.uk/pub/databases/genenames/hgnc/tsv/hgnc_complete_set.txt
def get_hgnc_id_symbol_map(input_path=HGNC_DATA_PATH) -> Dict[str, str]:
    """Get mapping between HGNC IDs (prefixed) and symbols"""
    d = {}
    df = pd.read_csv(input_path, sep='\t')
    for index, row in df.iterrows():
        d[row['hgnc_id']] = row['symbol']
    return d


def get_hgnc_symbol_id_map(input_path=HGNC_DATA_PATH) -> Dict[str, str]:
    """Get mapping between HGNC symbols (unprefixed) and IDs"""
    d = {}
    df = pd.read_csv(input_path, sep='\t')
    for index, row in df.iterrows():
        d[row['symbol']] = row['hgnc_id'].split(':')[1]  # split: hgnc_id is formatted as "hgnc:<id>"
    return d

def p2g_is_definitive(label: str) -> bool:
    """Is phenotype to gene association definitive?

    AKA doesn't have the special syntax asdescribed in: https://www.omim.org/help/faq#1_6

    1. Brackets, "[ ]", Non-diseases: indicate "nondiseases," mainly genetic variations that lead to apparently
    abnormal laboratory test values (e.g., dysalbuminemic euthyroidal hyperthyroxinemia).
    2. Braces, "{ }", Susceptibility: indicate mutations that contribute to susceptibility to multifactorial
    disorders (e.g., diabetes, asthma) or to susceptibility to infection (e.g., malaria).
    3. A question mark, "?", Provisionality: before the phenotype name indicates that the relationship between
    the phenotype and gene is provisional. More details about this relationship are provided in the comment field
    of the map and in the gene and phenotype OMIM entries.
    """
    return not any(label.startswith(x) for x in ['[', '{', '?'])


def get_phenotype_genes(gene_phenotypes: Dict[str, Dict]) -> Dict[str, List[Dict[str, str]]]:
    """Get Disease->Gene (& more Gene->Disease) relationships

    Collect phenotype MIMs & associated gene MIMs and relationship info
    """
    phenotype_genes: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    for gene_mim, gene_data in gene_phenotypes.items():
        for assoc in gene_data['phenotype_associations']:
            p_mim, p_lab, p_map_key, p_map_lab = assoc['phenotype_mim_number'], assoc['phenotype_label'], \
                assoc['phenotype_mapping_info_key'], assoc['phenotype_mapping_info_label']
            if not p_mim:  # not an association to another MIM; ignore
                continue  # see: https://github.com/monarch-initiative/omim/issues/78
            phenotype_genes[p_mim].append({
                'gene_id': gene_mim, 'phenotype_label': p_lab, 'mapping_key': p_map_key,
                'mapping_label': p_map_lab})
    return phenotype_genes

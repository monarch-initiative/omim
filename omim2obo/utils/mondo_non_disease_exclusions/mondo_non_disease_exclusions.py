"""Generates a Mondo intesional exclusions TSV file with non-diseases as its contents.

Resources:
- Symbols explanation: https://www.omim.org/help/faq#1_3
"""
from argparse import ArgumentParser

import pandas as pd


def gen_mondo_non_disease_exclusions(symbolic_prefixes_path: str, mim_titles_path: str, outpath: str) -> pd.DataFrame:
    """Generates a Mondo intesional exclusions TSV file with non-diseases as its contents."""
    # Read inputs
    symbols_df = pd.read_csv(symbolic_prefixes_path, sep='\t').fillna('')
    mims_header = ['Prefix', 'MIM Number', 'Preferred Title; symbol', 'Alternative Title(s); symbol(s)',
                   'Included Title(s); symbols']
    mims_df = pd.read_csv(mim_titles_path, sep='\t', comment='#', header=None, names=mims_header).fillna('')
    excludable_symbol_names = set(symbols_df[~symbols_df['can_be_disease_or_phenotype']]['name'])

    # Transform
    df = mims_df[mims_df['Prefix'].isin(excludable_symbol_names)][['MIM Number', 'Preferred Title; symbol']]\
        .rename(columns={'MIM Number': 'term_id', 'Preferred Title; symbol': 'term_label'}).sort_values('term_id')
    df['term_id'] = df['term_id'].apply(lambda x: f'OMIM:{x}')
    df['exclusion_reason'] = 'MONDO:excludeNonDisease'
    # todo: consider FALSE; will increase performance, and TRUE is just here as a failsafe.
    df['exclude_children'] = 'TRUE'

    # Save & return
    df.to_csv(outpath, sep='\t', index=False)
    return df


def cli():
    """Command line interface"""
    parser = ArgumentParser(
        prog="Mondo non-disease exclusions",
        description="Generates a Mondo intesional exclusions TSV file with non-diseases as its contents.")
    parser.add_argument(
        '-s', '--symbolic-prefixes-path', required=True,
        help='Path to a TSV of symbolic prefix characters, and information about them. Source: '
             'https://www.omim.org/help/faq#1_3')
    parser.add_argument('-t', '--mim-titles-path', required=True, help='Path to mimTitles.txt; list of OMIM terms.')
    parser.add_argument('-o', '--outpath', required=True, help='Path to save the output TSV.')
    gen_mondo_non_disease_exclusions(**vars(parser.parse_args()))


if __name__ == '__main__':
    cli()

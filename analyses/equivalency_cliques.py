"""Equivalency cliques analyses

Prerequisites
  - Files: Need to be pre-downloaded in data/.

Resources
  - GitHub issue: https://github.com/monarch-initiative/omim/issues/45

Areas for improvement
  - Dynamic term_id list: Instead of a static list, could do something dynamic, like figuring out which of these terms
  are connected via common equivalent gene node (e.g. through owl:equivalentClass, skos:exactMatch).
  - Reduce duplicate code: Pass files in config (Paths or names), headers, Term ID field.
  - Time of data: Get latest. It's possible these files are out of sync too; especially allelicVariants.tsv.

Areas for possible redisign
  - Tidy/tall format?: Instead of `terms_with_common_data_field` being a delimited list, could make 1 row per entry.
"""
import os
from copy import copy
from typing import Any, Dict, List

import pandas as pd


CONFIG = {
    'term_ids': [
        146910,
        147010,
        147070,
        146910,
        147070,
        147010,
        300015,
        402500,
        300151,
        403000,
        300162,
        400011,
        300357,
        400023,
        312095,
        465000,
        400020,
        312865,
        425000,
        306250,
        430000,
        308385,
        450000,
        313470,
        609517,
        610067,
    ],
    'data_dir_path': os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'data')
}


def _move_columns_to_left(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    """Reorganizes such that columns listed will appear first
    Another way to do: https://www.geeksforgeeks.org/how-to-move-a-column-to-first-position-in-pandas-dataframe/"""
    tail = list(df.columns)
    for col in cols:
        tail.remove(col)
    df = df[cols + tail]
    return df


def _find_common_data(
    df: pd.DataFrame, pk: str, common_data_field: str, terms_with_common_data_field: str,
    terms_with_common_data_delimiter: str, move_cols_to_left=True
):
    """Find terms that are linked to the same data."""
    # Initialize new column
    if terms_with_common_data_field not in list(df.columns):
        df[terms_with_common_data_field] = ''
    if move_cols_to_left:
        df = _move_columns_to_left(df, [pk, common_data_field, terms_with_common_data_field])

    common_data_terms: Dict[Any, List[Any]] = {}
    for _index, row in df.iterrows():
        term = row[pk]
        common_data = row[common_data_field]
        if common_data not in common_data_terms:
            common_data_terms[common_data] = []
        common_data_terms[common_data].append(term)

    for index, row in df.iterrows():
        terms: List[Any] = copy(common_data_terms[row[common_data_field]])
        terms.remove(row[pk])
        terms: List[str] = [str(x) for x in terms]
        terms: str = terms_with_common_data_delimiter.join(terms)
        df.at[index, terms_with_common_data_field] = terms

    return df


def run(
    term_ids: List[int],
    data_dir_path: str,
    pk='MIM Number',
    common_data_field='Approved Gene Symbol (HGNC)',
    terms_with_common_data_field='Terms w common HGNC symbol',
    terms_with_common_data_delimiter=';'
) -> pd.DataFrame:
    """run analysis

    term_ids: List of OMIM ids.
    data_dir_path: Path where all the data files are stored.
    pk: Common primary key used in all data files.
    common_data_field: Field containing data that certain entries may share common links to. E.g. two MIM entries might be
      linked to the same gene.
    """
    # Collect data
    table_path__mim_titles = os.path.join(data_dir_path, 'mimTitles.tsv')
    table_path__mim2gene = os.path.join(data_dir_path, 'mim2gene.tsv')
    # table_path__genemap2 = os.path.join(data_dir_path, 'genemap2.tsv')
    # table_path__allelic_variants = os.path.join(data_dir_path, 'allelicVariants.tsv')
    # table_path__morbidmap = os.path.join(data_dir_path, 'morbidmap.tsv')
    # table_path__phenotypic_series = os.path.join(data_dir_path, 'phenotypicSeries.tsv')
    table__mim_titles = pd.read_csv(table_path__mim_titles, sep='\t', comment='#')
    table__mim2gene = pd.read_csv(table_path__mim2gene, sep='\t', comment='#')
    # todo #1a: utilize other files if/as needed
    # table__genemap2 = pd.read_csv(table_path__genemap2, sep='\t', comment='#')
    # table__allelic_variants = pd.read_csv(table_path__allelic_variants, sep='\t', comment='#')
    # table__morbidmap = pd.read_csv(table_path__morbidmap, sep='\t', comment='#')
    # table__phenotypic_series = pd.read_csv(table_path__phenotypic_series, sep='\t', comment='#')

    # todo: table__mim2gene: entrez gene ID should be int or string without .0's
    # Formatting
    pass

    # Initialize dataframe and filter what's needed
    df = table__mim_titles[table__mim_titles['MIM Number'].isin(term_ids)]
    # df = _move_columns_to_left(df, [pk])

    # JOIN primary data
    df = pd.merge(df, table__mim2gene, on=pk, how='left')
    # df = _move_columns_to_left(df, [pk, common_data_field])

    # Find terms that link to the same categorical data
    df = _find_common_data(df, pk, common_data_field, terms_with_common_data_field, terms_with_common_data_delimiter)

    # todo #1b: add more fields from other df's if needed
    pass

    # Sort
    df = df.sort_values(common_data_field)

    # Save and return
    df.to_csv(os.path.join(data_dir_path, '..', 'equivalency_cliques.csv'), index=False)
    return df


if __name__ == '__main__':
    run(**CONFIG)

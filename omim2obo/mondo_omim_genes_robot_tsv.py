"""Create: ROBOT template of Mondo and OMIM gene relations: relational information for gene and disease classes"""
from argparse import ArgumentParser
from pathlib import Path
from typing import Dict, Union

import pandas as pd

from omim2obo.utils.utils import remove_angle_brackets


ROBOT_SUBHEADER = {
    'mondo_id': 'ID',
    'hgnc_id': "SC 'has material basis in germline mutation in' some %",
    'omim_disease_xref': '>A oboInOwl:source',
    'omim_gene': '',
}


def mondo_omim_genes_robot_tsv(inpath: Union[Path, str], outpath: Union[Path, str]) -> pd.DataFrame:
    """Create: ROBOT template of Mondo and OMIM gene relations"""
    df = pd.read_csv(inpath, sep='\t')

    # Remove the first character, a question mark (?), from each field in the header; an artefact of the SPARQL query.
    df.rename(columns={col: col[1:] for col in df.columns if col.startswith('?')}, inplace=True)

    # Remove < and > characters from specified columns
    uri_cols = ['mondo_id', 'hgnc_id', 'omim_gene']
    for col in uri_cols:
        df[col] = remove_angle_brackets(list(df[col]))

    # Format col order
    df = df[['mondo_id', 'hgnc_id', 'omim_disease_xref', 'omim_gene']]

    # Sort
    df = df.sort_values(by=['mondo_id', 'hgnc_id', 'omim_gene', 'omim_disease_xref'])

    # Remove cases where >1 gene association
    # - These indicate non-causal relationships, which we don't care about.
    df = df[~df['omim_disease_xref'].duplicated(keep=False)]

    # Insert ROBOT subheader
    df = pd.concat([pd.DataFrame([ROBOT_SUBHEADER]), df])

    df.to_csv(outpath, sep='\t', index=False)
    return pd.DataFrame()


def cli():
    """Command line interface."""
    parser = ArgumentParser(
        prog='mondo-genes-robot-tsv',
        description='Create a ROBOT template TSV of relational information for gene and disease classes')
    parser.add_argument(
        '-i', '--inpath', required=True,
        help='Path to file with such relational information, but not yet formatted as a ROBOT template.')
    parser.add_argument(
        '-o', '--outpath', required=True,
        help='Path to save output.')
    d: Dict = vars(parser.parse_args())
    mondo_omim_genes_robot_tsv(**d)


if __name__ == '__main__':
    cli()

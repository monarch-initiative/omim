"""Misc utilities"""
from typing import Dict, List, Optional, Tuple, Union

import pandas as pd
from rdflib import URIRef

from omim2obo.config import DISEASE_GENE_EXCLUSIONS_PATH, DISEASE_GENE_PROTECTED_PATH
from omim2obo.namespaces import ORCID


# todo: also in mondo-ingest. Refactor into mondolib: https://github.com/monarch-initiative/mondolib/issues/13
def remove_angle_brackets(uris: Union[str, List[str]]) -> Union[str, List[str]]:
    """Remove angle brackets from URIs, e.g.:
    <https://omim.org/entry/100050> --> https://omim.org/entry/100050"""
    str_input = isinstance(uris, str)
    uris = [uris] if str_input else uris
    uris2 = []
    for x in uris:
        x = x[1:] if x.startswith('<') else x
        x = x[:-1] if x.endswith('>') else x
        uris2.append(x)
    return uris2[0] if str_input else uris2


def get_d2g_digenic_protections(
    path=DISEASE_GENE_PROTECTED_PATH
) -> Dict[Tuple[str, str], Tuple[str, Optional[URIRef]]]:
    """Get information for manually curated disease-gene association protections.

    Protections are associatiosn we want to add even if they (no longer) appear in the OMIM source data.

    :return: Dictionary with (phenotype MIM, gene MIM) keys and (HGNC id, curator ORCID) values.
    """
    df = pd.read_csv(path, sep='\t').fillna('')
    for col in ['phenotype_mim', 'gene_mim', 'hgnc_id']:
        df[col] = df[col].apply(lambda x: x.split(':')[1])
    return {
        (x['phenotype_mim'], x['gene_mim']): (x['hgnc_id'], ORCID[x['orcid']] if x['orcid'] else None)
        for x in df.to_dict(orient='records')
    }


def get_d2g_exclusions_by_curator(path=DISEASE_GENE_EXCLUSIONS_PATH) -> Dict[str, Optional[URIRef]]:
    """Get disease-gene exclusions

    Situations where the pipeline logic would otherwise keep a disease-gene association, we want to exclude it.

    :return: Dict[str, str]: Phenotype MIM as keys, ORCID of curator as values
    """
    df = pd.read_csv(path, sep='\t').fillna('')
    df['omim_id'] = df['omim_id'].apply(lambda x: x.split(':')[1])
    phenotype_mim_orcid_map = {x['omim_id']: x['orcid'] for x in df.to_dict(orient='records')}
    return {k: ORCID[v] if v else None for k, v in phenotype_mim_orcid_map.items()}

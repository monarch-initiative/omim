"""Misc utilities"""
from typing import List, Union


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

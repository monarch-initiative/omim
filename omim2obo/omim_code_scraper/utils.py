"""Code scraping project utilities"""
from typing import List


def get_codes_without_prefixes(code_tuples: List[tuple]) -> List[str]:
    """Get codes without their prefixes"""
    codes: List[str] = [x[1] for x in code_tuples]
    return codes

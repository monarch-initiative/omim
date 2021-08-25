"""OMIM Data Pipeline: Stats importer
- Imports stats from: https://omim.org/statistics/update

TODO's
Minor
- outpath
  - Save to outpath
  - If filename not in path, create one
- Validate
  - outpath: include checking if os.path.exists or w/e for outpath
  - yyyy_mm: finish validation
- yyyy_mm: accept list; query multiple yyyy/mm args
- Pipenv: use
"""
from typing import List

import requests
# noinspection PyProtectedMember
from bs4 import BeautifulSoup, ResultSet

from omim_code_scraper.config import STATS_PAGES_URL_BASE
from omim_code_scraper.definitions.error import OmimDataPipelineError


def validate_args(yyyy_mm):
    """Ensure arguments syntactically and logically valid"""
    # Abritrary/temp to resolve usage warning for now
    err_msg_list: List[str] = []
    err_yyyy_mm = 'Invalid syntax for YYYY/MM argument. Needs to be 4-digit ' \
        'integer for year, followed by /, followed by 2-digit integer for ' \
        'month.'
    if not yyyy_mm.__contains__('/'):
        err_msg_list.append(err_yyyy_mm)
    # TODO: Next, split and check that each side is an integer. don't append the
    # same error if it already exists in the list.

    if len(err_msg_list) > 0:
        raise OmimDataPipelineError(str(err_msg_list))


def get_codes_by_yyyy_mm(yyyy_mm: str, outpath: str = '') -> List[tuple]:
    """Omim data pipeline: Stats importer: Get codes by year/month

    Args:
        yyyy_mm (type): Year and month in format of YYYY/MM
        outpath (str): Path to save output file. If not present, same directory
            of any input files passed will be used.
    """
    # Get data
    year, month = yyyy_mm.split('/')[0], yyyy_mm.split('/')[1]
    url = '/'.join([STATS_PAGES_URL_BASE, year, str(int(month))])
    # noinspection PyUnresolvedReferences
    headers = requests.utils.default_headers()
    headers.update({'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0', })
    page = requests.get(url, headers=headers)
    soup = BeautifulSoup(page.text, 'html.parser')
    elements: ResultSet = soup.find_all('span', {'class': 'mim-font mim-hint'})

    # Parse
    code_str_list: List[str] = [x.text.strip() for x in elements]
    code_tuple_list: List[tuple] = []
    for code in code_str_list:
        if code[0].isnumeric():
            code_tuple_list.append(tuple(['', code]))
        else:
            code_tuple_list.append(tuple([code[0], code[1:]]))

    # Return
    if not outpath:
        return code_tuple_list
    else:
        pass  # TODO: save

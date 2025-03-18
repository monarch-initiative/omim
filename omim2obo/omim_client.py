"""OMIM API client"""
import os
from dataclasses import dataclass
from typing import List
import requests
import logging
import re
import time

from omim2obo.config import CACHE_INCOMPLETENESS_INDICATOR_PATH, CACHE_LAST_UPDATED_PATH

MAX_TOTAL = 5000
BATCH_SIZE = 100
OMIM_API = 'https://api.omim.org/api/entry'

LOG = logging.getLogger('OmimClient')
# todo: alternatively, could print a short message and then prompt the user to read a tagged message in dev docs
RATE_ERR = ('Total MIMs to fetch exceeds the expected daily API rate limit of {}. For now, will only fetch up to that' 
    ' limit.\n\nThe following fetching and caching strategy is set up thusly: For now, as many MIMs as possible up to '
    'this limit wll be fetched and data for them will be cached. When this process runs subsequently, it will pick up '
    'where it left off, fetching only the MIMs that have not yet been fetched. Until it is detected that all MIMs have '
    'been fetched, a temporary file {} will be saved to indicate this status. It will '
    'be deleted when all MIMs have been fetched. Also, the date of the cache will be saved in {}. The date that will '
    'be set will be the date that this fetching started, not the date that it completed. This is in order to account '
    'for the possibility that a MIM\'s data might be updated between the start and end date of this initial setup '
    'process.\n\nAfter this initial setup is complete, the cache will be regularly updated in a different way, no more '
    'than 1x/month.\n\nAdvice: After this run compeltes, to manually fetch regularly, no more than 1x/day, until are '
    'data for all MIMs has been fetched.')

@dataclass
class OmimClient:
    """OMIM API client"""

    api_key: str
    omim_ids: List[str]
    start: int = 0
    total: int = -1

    # TODO: what to do about MAX_TOTAL = 5k? how to know if cache is in valid state for having fetched all?
    # TODO: what if i save all of them and want to pick up tomorrow? but what if i don't pick up 3 months from now? but
    #  what if a MIM is updated between now and then? i want the valid date to be at the BEGINNING of fetching
    #  everything in the cache
    # TODO: perhaps I can save a temp file for initial-cache-incomplete.txt or something. and whenever it runs, it reads
    #  the existing files, gets set of MIMs cached (in regular TSVs). then uses set op to figure out what still needs
    #  to be fetched
    # TODO: do I save the date here or in the calling func?
    #  - Should be date when this process started
    def fetch_all(self):
        """Fetch all MIMs"""
        if self.total < 0:
            self.total = len(self.omim_ids)

        # Handle when requested total exceeds expected daily rate limit
        cache_complete_on_fetch_completion = True
        if self.total > MAX_TOTAL:
            cache_complete_on_fetch_completion = False
            LOG.warning(RATE_ERR.format(MAX_TOTAL, CACHE_INCOMPLETENESS_INDICATOR_PATH, CACHE_LAST_UPDATED_PATH))
            with open(CACHE_INCOMPLETENESS_INDICATOR_PATH, 'w') as file:
                file.write('')
        total_to_fetch = min(self.total, MAX_TOTAL)

        count = 0
        result = []
        while count < self.start + total_to_fetch:
            current = self.start + count
            end = self.start + min(count + BATCH_SIZE, total_to_fetch)
            ids = self.omim_ids[current:end]
            entries = self.fetch_ids(ids)
            if entries:
                result += entries
            else:
                LOG.warning(f'Failed after {count} records were fetched')
                break
            time.sleep(2)
            count += BATCH_SIZE
        if cache_complete_on_fetch_completion and os.path.exists(CACHE_INCOMPLETENESS_INDICATOR_PATH):
            os.remove(CACHE_INCOMPLETENESS_INDICATOR_PATH)
        return result

    def fetch_ids(self, ids):
        """Fetch given MIMs"""
        params = {'format': 'json', 'apiKey': self.api_key, 'mimNumber': ','.join(ids), 'include': 'all'}
        response = requests.get(OMIM_API, params)
        if response.status_code >= 400:
            if response.status_code == 403:  # request rejected
                LOG.warning('Request rejected: ')
                msg = 'API key not valid' if re.search(r'The API key: .* is inactive', response.text) else response.txt
                LOG.warning(msg)
            print()  # TODO temp: debug if this happens, else remove this clause
            raise RuntimeError(f'Failed to fetch OMIM entries: {response.text}')

        resp = response.json()
        entries = resp['omim']['entryList']
        return entries

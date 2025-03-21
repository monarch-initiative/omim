"""OMIM API client"""
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import requests
import logging
import re
import time

from omim2obo.config import CACHE_INCOMPLETENESS_INDICATOR_PATH, CACHE_LAST_UPDATED_PATH

# BATCH_SIZE: Don't change!
#  https://omim.org/help/api: "Entries and clinical synopses are limited to 20 per request if any 'includes' are
#  specified, otherwise there is no limit." There are docs on that page for "includes". We set "include" to "all".
#  However, even if this param is left out, it looks like the default behavior is "all" anyway, and it still limits to
#  a maximum of 20/request.
BATCH_SIZE = 20
OMIM_API = 'https://api.omim.org/api/entry'

LOG = logging.getLogger('OmimClient')
# todo: alternatively, could print a short message and then prompt the user to read a tagged message in dev docs
RATE_ERR = ('Rate limit error: MIMs fetched exceeded allowable API limit(normally 5,000).\n\n'
    'The following fetching and caching strategy is set up thusly: For now, as many MIMs as possible up to '
    'this limit wll be fetched and data for them will be cached. When this process runs subsequently, it will pick up '
    'where it left off, fetching only the MIMs that have not yet been fetched. Until it is detected that all MIMs have '
    'been fetched, a temporary file {} will be saved to indicate this status. It will be deleted when all MIMs have '
    'been fetched. Also, the date of the cache will be saved in {}. The date that will be set will be the date that '
    'this fetching started, not the date that it completed. This is in order to account for the possibility that a '
    'MIM\'s data might be updated between the start and end date of this initial setup process.\n\n'
    'After this initial setup is complete, the cache will be regularly updated in a different way, no more '
    'than 1x/month.\n\n'
    'Advice: After this run completes, you should manually fetch regularly, no more than 1x/day, until data for all '
    'MIMs has been fetched.'.format(CACHE_INCOMPLETENESS_INDICATOR_PATH, CACHE_LAST_UPDATED_PATH))

def _log_incomplete_seed_run():
    """Write to disk an indication that the seed run was incomplete.

    The "seed run" means the initial creation of the cache. The way it works is that if there exists no cache, we will
    fetch all MIMs. Subsequent fetches after the seed run will only fetch since the last fetch date, so it's important
    that we know if the initial cache is complete.
    """
    with open(CACHE_INCOMPLETENESS_INDICATOR_PATH, 'w') as file:
        file.write('')


@dataclass
class OmimClient:
    """OMIM API client"""
    api_key: str
    omim_ids: List[str]
    start: int = 0
    total: int = -1

    def fetch_all(self, seed_run=False):
        """Fetch all MIMs"""
        count = 0
        results = []
        fetch_success = True
        self.total = len(self.omim_ids) if self.total < 0 else self.total
        while count < self.start + self.total:
            current = self.start + count
            end = self.start + min(count + BATCH_SIZE, self.total)
            ids = self.omim_ids[current:end]
            entries, err = self.fetch_ids(ids)
            if seed_run and (err or not entries):
                _log_incomplete_seed_run()
            if err == 'rate-limit':
                LOG.warning(f'Records fetched: {count} of {self.total}')
                LOG.warning(RATE_ERR)
                fetch_success = False
                break
            # todo: Ideally would also be good to cache what we received to this point as well, as with the 'rate-limit'
            #  case, then throw error in calling func
            elif err:
                raise RuntimeError(err)
            elif not entries:
                raise RuntimeError(f'Query on ids {ids} returned no results.')
            results += entries
            time.sleep(2)  # todo: is this necessary?
            count += BATCH_SIZE

        # Update cache data
        # Incompleteness indicator: If fetch was successful and the indicator exists, remove it
        if fetch_success and os.path.exists(CACHE_INCOMPLETENESS_INDICATOR_PATH):
            os.remove(CACHE_INCOMPLETENESS_INDICATOR_PATH)
        # Date: If it is a seed run, only update it the first time. Ensures no cached entries are outdated when complete
        if not seed_run or (seed_run and not os.path.exists(CACHE_LAST_UPDATED_PATH)):
            with open(CACHE_LAST_UPDATED_PATH, 'w') as file:
                file.write(datetime.now().strftime("%Y-%m-%d"))  # YYYY-MM-DD

        return results

    def fetch_ids(self, ids: List[str], seed_run=False) -> Tuple[List[Dict], Optional[str]]:
        """Fetch given MIMs

        :returns List of entries, and a string error message if an error occurred (else None)
        todo: If error occurs, better pattern is probably raising error and including the data
        """
        params = {'format': 'json', 'apiKey': self.api_key, 'mimNumber': ','.join(ids), 'include': 'all'}
        response = requests.get(OMIM_API, params)

        if response.status_code >= 400:  # error
            if seed_run:
                _log_incomplete_seed_run()
            # 403=request rejected,
            if response.status_code == 403 and re.search(r'The API key: .* is inactive', response.text):
                return [], 'Invalid API key'
            # 429=too many requests (rate limiting)
            elif response.status_code == 429:
                return [], 'rate-limit'  # Don't halt execution; expected. Will print guidance.
            return [], response.text  # Halt execution because unexpected

        resp: Dict = response.json()
        entries: List[Dict] = resp['omim']['entryList']
        return entries, None

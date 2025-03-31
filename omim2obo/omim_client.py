"""OMIM API client

OMIM docs: https://omim.org/help/api
"""
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
OMIM_ENTRY_API_URL = 'https://api.omim.org/api/entry'
OMIM_ENTRY_SEARCH_API_URL = OMIM_ENTRY_API_URL + '/search'

LOG = logging.getLogger('OmimClient')
# todo: alternatively, could print a short message and then prompt the user to read a tagged message in dev docs
RATE_ERR = ('Rate limit error: MIMs fetched exceeded allowable API limit(normally 5,000).\n\n'
    'The following fetching and caching strategy is set up thusly: For now, as many MIMs as possible up to this limit '
    'will be fetched and data for them will be cached. When this process runs subsequently, it will pick up where it '
    'left off, fetching only the MIMs that have not yet been fetched. Until it is detected that all MIMs have been '
    'fetched, a temporary file {} will be saved to indicate this status. It will be deleted when all MIMs have been '
    'fetched. Also, the since_date of the cache will be saved in {}. The since_date that will be set will be the '
    'since_date that this fetching started, not the since_date that it completed. This is in order to account for the '
    'possibility that a MIM\'s data might be updated between the start and end since_date of this initial setup '
    'process.\n\n'
    'After this initial setup is complete, the cache will be regularly updated in a different way, no more '
    'than 1x/month.\n\n'
    'Advice: After this run completes, you should manually fetch regularly, no more than 1x/day, until data for all '
    'MIMs has been fetched.'.format(CACHE_INCOMPLETENESS_INDICATOR_PATH, CACHE_LAST_UPDATED_PATH))

def _log_incomplete_seed_run():
    """Write to disk an indication that the seed run was incomplete.

    The "seed run" means the initial creation of the cache. The way it works is that if there exists no cache, we will
    fetch all MIMs. Subsequent fetches after the seed run will only fetch since the last fetch since_date, so it's
    important that we know if the initial cache is complete.
    """
    with open(CACHE_INCOMPLETENESS_INDICATOR_PATH, 'w') as file:
        file.write('')


@dataclass
class OmimClient:
    """OMIM API client

    todo: redundancies w/ _batch_and_fetch & _fetch_since_date()?. Ideally DRY up.
    todo: might be possible to save bandwidth by filtering return fields
    todo: Ideally would have a way to get around rate limit for non seed-running, e.g. in the event that the script
     does not run weekly and instead several months or years pass. The workaround to this is to just re-initialize the
     cache by deleting the cache files and re-running the build.
    todo: For the raise RuntimeError situations in the fetch_since_date and fetch_ids methods, ideally would also be
     good to cache what we received to this point as well for these unanticipated exceptions, as with the 'rate-limit'
     case, then throw error in calling func.
    todo: are the sleep(2)s necessary? or could we reduce?
    """
    api_key: str
    start: int = 0
    total: int = -1

    def fetch(self, ids: List[str] = None, since_date: datetime = None, seed_run=False, verbose=True) -> List[Dict]:
        """Fetch MIM entry data from the OMIM API. Can query by explicit IDs, or since since_date."""
        results: List[Dict] = []
        if ids and since_date:
            raise ValueError('Cannot specify both ids and since_date')
        elif not (ids or since_date):
            raise ValueError('Must specify either ids or since_date')
        elif since_date and seed_run:
            raise ValueError('Cannot specify since_date and seed_run')
        elif ids:
            if verbose:
                print(f'- Fetching {len(ids)} MIMs from OMIM entry API')
            results = self._fetch_ids(ids, seed_run)
        elif since_date:
            if verbose:
                print(f'- Fetching MIMs since {str(since_date)} from OMIM entry API')
            results = self._fetch_since_date(since_date)
        if verbose:
            msg = f'- Fetched data for {len(results)} MIMs. Saving results.' if len(results) > 0 else \
                '- API showing that there are no newly updated MIMs since last fetch.'
            print(msg)
        return [x['entry'] for x in results]

    def _fetch_since_date(self, since_date: datetime) -> List[Dict]:
        """Fetch all MIMs since the given since_date

        Relevant OMIM docs: https://omim.org/help/search
        """
        since_date_str = datetime.strftime(since_date, "%Y/%m/%d")
        to_date_str = datetime.strftime(datetime.now(), "%Y/%m/%d")
        static_query_params = f'?search=*:*&filter=date_updated:{since_date_str}-{to_date_str}' + \
            f'&sort=score+desc,+prefix_sort+desc&limit={BATCH_SIZE}&format=json'
        i = 0
        results: List[Dict] = []
        while True:
            # Set up
            start_query_parm = '&start=' + str(i)
            url = OMIM_ENTRY_SEARCH_API_URL + static_query_params + start_query_parm
            response_dict, err = self._request(url, {'apiKey': self.api_key})
            # Query
            entries: List[Dict] = response_dict.get('searchResponse', {}).get('entryList', [])
            results += entries
            i += BATCH_SIZE
            # Error handling
            if err == 'rate-limit':
                LOG.warning(f'Records fetched: {len(results)}')
                LOG.warning(RATE_ERR)
                break
            elif err:
                raise RuntimeError(err)
            elif not entries or len(entries) < BATCH_SIZE:  # fetched everything
                break
            time.sleep(2)

        ids: List[str] = [x['entry']['mimNumber'] for x in results]
        return self._fetch_ids(ids)

    def _fetch_ids(self, ids: List[str] = None, seed_run=False) -> List[Dict]:
        """Fetch all MIMs"""
        count = 0
        results: List[Dict] = []
        fetch_success = True
        self.total = len(ids) if self.total < 0 else self.total
        while count < self.start + self.total:
            # Set up
            current = self.start + count
            end = self.start + min(count + BATCH_SIZE, self.total)
            ids_i = ids[current:end]
            params = {'format': 'json', 'apiKey': self.api_key, 'mimNumber': ','.join(ids_i), 'include': 'all'}
            # Query
            response_dict, err = self._request(OMIM_ENTRY_API_URL, params, seed_run)
            entries: List[Dict] = response_dict.get('entryList', [])
            results += entries
            count += BATCH_SIZE
            # Error handling
            if seed_run and (err or not entries):
                _log_incomplete_seed_run()
            if err == 'rate-limit':
                LOG.warning(f'Records fetched: {count} of {self.total}')
                LOG.warning(RATE_ERR)
                fetch_success = False
                break
            elif err:
                raise RuntimeError(err)
            elif len(entries) != len(ids_i):
                raise RuntimeError(f'Query on ids {ids_i} returned {len(entries)} results, but expected {len(ids_i)}.')
            elif not entries:
                raise RuntimeError(f'Query on ids {ids_i} returned no results.')
            time.sleep(2)

        # Update cache data
        # Incompleteness indicator: If fetch was successful and the indicator exists, remove it
        if fetch_success and os.path.exists(CACHE_INCOMPLETENESS_INDICATOR_PATH):
            os.remove(CACHE_INCOMPLETENESS_INDICATOR_PATH)
        # Date: If it is a seed run, only update it the first time. Ensures no cached entries are outdated when complete
        if not seed_run or (seed_run and not os.path.exists(CACHE_LAST_UPDATED_PATH)):
            with open(CACHE_LAST_UPDATED_PATH, 'w') as file:
                file.write(datetime.now().strftime("%Y-%m-%d"))  # YYYY-MM-DD

        return results

    @staticmethod
    def _request(url: str, params: Dict = {}, seed_run=False) -> Tuple[Dict, Optional[str]]:
        """Submit reques to OMIM API, and handle errors.
        todo: If error occurs, better pattern is probably raising error and including the data
        """
        response = requests.get(url, params)
        if response.status_code >= 400:  # error
            if seed_run:
                _log_incomplete_seed_run()
            # 403=request rejected,
            if response.status_code == 403 and re.search(r'The API key: .* is inactive', response.text):
                return {}, 'Invalid API key'
            # 429=too many requests (rate limiting)
            elif response.status_code == 429:
                return {}, 'rate-limit'  # Don't halt execution; expected. Will print guidance.
            return {}, response.text  # Halt execution because unexpected

        return response.json()['omim'], None

from dataclasses import dataclass
from typing import List
import requests
import logging
import re
import time

MAX_TOTAL = 5000
BATCH_SIZE = 20
OMIM_API = 'https://api.omim.org/api/entry'

LOG = logging.getLogger('OmimClient')


@dataclass
class OmimClient:
    api_key: str
    omim_ids: List[str]
    start: int = 0
    total: int = -1

    def fetch_all(self):
        if self.total < 0:
            self.total = len(self.omim_ids)
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
        return result

    def fetch_ids(self, ids):
        params = {'format': 'json', 'apiKey': self.api_key, 'mimNumber': ','.join(ids), 'include': 'all'}
        try:
            response = requests.get(OMIM_API, params)
            if response.status_code == 403:  # request rejected
                LOG.warning('Request rejected: ')
                if re.search(r'The API key: .* is inactive', response.text):
                    LOG.warning('    API key not valid')
                else:
                    LOG.warning(response.text)
                return None
            resp = response.json()
        except Exception as err:
            LOG.error(f'Error occurred: {err}.')
            return None

        entries = resp['omim']['entryList']
        return entries



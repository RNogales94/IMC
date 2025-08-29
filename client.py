from dataclasses import dataclass
from datetime import datetime, date
from typing import List, Optional

import requests


@dataclass
class Launch:
    id: str
    launch_time: datetime
    payload_ids: List[str]


class SpaceXClient:
    def __init__(self, base_url: str = 'https://api.spacexdata.com/v4'):
        self.base_url = base_url

    def _url(self, path: str) -> str:
        return f'{self.base_url}/{path}'

    # TODO: Implement Task 1 here
    def get_launches(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[Launch]:
        resp = requests.post(
            url=self._url('launches/query'),
            json={
                'query': {},
                'options': {
                    'select': ['id', 'date_unix', 'payloads'],
                    'pagination': False
                }
            }
        )
        resp.raise_for_status()
        return [
            Launch(id=launch['id'],
                   launch_time=datetime.utcfromtimestamp(launch['date_unix']),
                   payload_ids=launch['payloads'])
            for launch in resp.json()['docs']
        ]

    # TODO: Implement Task 2 here
    def get_heaviest_launch(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> Optional[Launch]:
        raise NotImplementedError

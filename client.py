from dataclasses import dataclass
from datetime import datetime, date, timedelta, timezone
from typing import List, Optional

import requests


@dataclass
class Launch:
    id: str
    launch_time: datetime
    payload_ids: List[str]
    total_payload_mass_kg: Optional[float] = None

class SpaceXClient:
    def __init__(self, base_url: str = 'https://api.spacexdata.com/v4'):
        self.base_url = base_url

    def _url(self, path: str) -> str:
        return f'{self.base_url}/{path}'

    def get_launches(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[Launch]:
        """
        Return launches within the date range [start_date, end_date], both treated as full days (UTC).
        - If start_date is None: no lower bound.
        - If end_date is None: no upper bound.
        - If start_date > end_date: return an empty list.
        Implementation detail:
        We treat each bound as the whole day in UTC by filtering `date_unix`:
            * lower bound:  >= start_date at 00:00:00 UTC
            * upper bound:  <  (end_date + 1 day) at 00:00:00 UTC
        This makes the end day inclusive without dealing with 23:59:59.
        """
        if start_date and end_date and start_date > end_date:
            return []

        # Build a unix-timestamp filter on `date_unix` in UTC
        date_unix_filter = {}
        if start_date:
            start_utc_midnight = datetime(start_date.year, start_date.month, start_date.day, tzinfo=timezone.utc)
            date_unix_filter["$gte"] = int(start_utc_midnight.timestamp())

        if end_date:
            end_plus_one_day = end_date + timedelta(days=1)
            end_next_day_utc_midnight = datetime(
                end_plus_one_day.year, end_plus_one_day.month, end_plus_one_day.day, tzinfo=timezone.utc
            )
            date_unix_filter["$lt"] = int(end_next_day_utc_midnight.timestamp())

        query_body = {}
        if date_unix_filter:
            query_body["date_unix"] = date_unix_filter

        resp = requests.post(
            url=self._url('launches/query'),
            json={
                'query': query_body,
                'options': {
                    'select': ['id', 'date_unix', 'payloads'],
                    'pagination': False
                }
            }
        )
        resp.raise_for_status()

        docs = resp.json().get('docs', [])

        # Build result list (keep datetime as timezone-aware UTC for Py 3.9)
        launches: List[Launch] = [
            Launch(
                id=doc["id"],
                launch_time=datetime.fromtimestamp(int(doc["date_unix"]), tz=timezone.utc),
                payload_ids=doc.get("payloads") or [],
            )
            for doc in docs
            if doc.get("id") is not None and doc.get("date_unix") is not None
        ]

        return launches

    def get_heaviest_launch(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Optional[Launch]:
        """
        - Returns the heaviest launch in the period, an object of Launch class or None
        - Relies on `populate` to include payloads with { id, mass_kg }
        - If any payload happens to be just a string ID, it counts as 0 kg
        - The Launch object returned has an extra attribute `total_payload_mass_kg` with the total mass
        """
        if start_date and end_date and start_date > end_date:
            return None

        date_unix_filter = {}
        if start_date:
            start_utc = datetime(start_date.year, start_date.month, start_date.day, tzinfo=timezone.utc)
            date_unix_filter["$gte"] = int(start_utc.timestamp())
        if end_date:
            end_plus_one = end_date + timedelta(days=1)
            end_utc = datetime(end_plus_one.year, end_plus_one.month, end_plus_one.day, tzinfo=timezone.utc)
            date_unix_filter["$lt"] = int(end_utc.timestamp())

        query_body = {"date_unix": date_unix_filter} if date_unix_filter else {}

        resp = requests.post(
            url=self._url("launches/query"),
            json={
                "query": query_body,
                "options": {
                    "select": ["id", "date_unix", "payloads"],
                    "populate": [{"path": "payloads", "select": ["id", "mass_kg"]}],
                    "pagination": False
                }
            },
            timeout=20
        )
        resp.raise_for_status()
        launches = resp.json().get("docs", [])

        if not launches:
            return None

        heaviest_doc = None
        heaviest_mass = None

        for launch in launches:
            # Sum payload masses; populated entries are dicts with mass_kg
            total_mass = 0.0
            for p in (launch.get("payloads") or []):
                if isinstance(p, dict):
                    total_mass += float(p.get("mass_kg") or 0.0) # None or missing will be 0.0 kg (this is an assumption)

            if heaviest_mass is None or total_mass > heaviest_mass:
                heaviest_mass = total_mass
                heaviest_doc = launch

        if not heaviest_doc:
            return None

        # Build Launch domain object
        launch_time = datetime.fromtimestamp(int(heaviest_doc["date_unix"]), tz=timezone.utc)
        payload_ids: List[str] = [
            (p["id"] if isinstance(p, dict) else p)
            for p in (heaviest_doc.get("payloads") or [])
        ]
        launch = Launch(id=heaviest_doc["id"], launch_time=launch_time, payload_ids=payload_ids, total_payload_mass_kg=heaviest_mass)
        return launch
        
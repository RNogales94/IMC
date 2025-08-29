# test_client.py
import unittest
from datetime import date, datetime, timezone
import requests

from client import SpaceXClient

# Simple utility to stub requests.post
class DummyResp:
    def __init__(self, docs):
        self._docs = docs
    def json(self):
        # API always returns {"docs": [...]}
        return {"docs": self._docs}
    def raise_for_status(self):
        return None

class ClientTests(unittest.TestCase):
    def setUp(self):
        self.orig_post = requests.post
        self.client = SpaceXClient()

    def tearDown(self):
        requests.post = self.orig_post

    def test_get_launches_inclusive_range(self):
        # Inclusive range: 2018-02-01 <= date <= 2018-02-28
        # Three docs: on the 1st, 15th and 28th of Feb 2018 (UTC)
        docs = [
            {"id": "LAUNCH_FEB01", "date_unix": int(datetime(2018, 2, 1, 12, 0, tzinfo=timezone.utc).timestamp()), "payloads": []},
            {"id": "LAUNCH_FEB15", "date_unix": int(datetime(2018, 2, 15, 8, 0, tzinfo=timezone.utc).timestamp()), "payloads": ["PAY_P1"]},
            {"id": "LAUNCH_FEB28", "date_unix": int(datetime(2018, 2, 28, 23, 59, tzinfo=timezone.utc).timestamp()), "payloads": ["PAY_P2", "PAY_P3"]},
        ]
        def fake_post(url, json=None, timeout=None):
            # We don't validate the body here, we just return the canned docs
            return DummyResp(docs)
        requests.post = fake_post

        launches = self.client.get_launches(start_date=date(2018, 2, 1), end_date=date(2018, 2, 28))
        self.assertEqual([l.id for l in launches], ["LAUNCH_FEB01", "LAUNCH_FEB15", "LAUNCH_FEB28"])
        # Sanity check: timezone-aware UTC datetimes
        self.assertEqual(launches[0].launch_time.tzinfo, timezone.utc)

    def test_get_launches_open_ended(self):
        # With no bounds, all docs should be returned
        docs = [
            {"id": "LAUNCH_OPEN_Z1", "date_unix": 1500000000, "payloads": []},
            {"id": "LAUNCH_OPEN_Z2", "date_unix": 1600000000, "payloads": []},
        ]
        def fake_post(url, json=None, timeout=None):
            return DummyResp(docs)
        requests.post = fake_post

        launches = self.client.get_launches()
        self.assertEqual(len(launches), 2)
        self.assertEqual(launches[0].id, "LAUNCH_OPEN_Z1")

    def test_get_heaviest_handles_null_mass_and_picks_max(self):
        # Doc1: payload mass None -> treated as 0.0
        # Doc2: two payloads 1.5 + 0.5 = 2.0 kg => should win
        docs = [
            {
                "id": "LAUNCH_NULL_ONLY",
                "date_unix": int(datetime(2022, 7, 15, 12, 0, tzinfo=timezone.utc).timestamp()),
                "payloads": [{"id": "PAY_NULL", "mass_kg": None}],
            },
            {
                "id": "LAUNCH_TWO_PAYLOADS",
                "date_unix": int(datetime(2022, 7, 20, 12, 0, tzinfo=timezone.utc).timestamp()),
                "payloads": [{"id": "PAY_1", "mass_kg": 1.5}, {"id": "PAY_2", "mass_kg": 0.5}],
            },
        ]
        def fake_post(url, json=None, timeout=None):
            # Simulates /launches/query with populate
            return DummyResp(docs)
        requests.post = fake_post

        heavy = self.client.get_heaviest_launch(start_date=date(2022, 7, 1), end_date=date(2022, 7, 31))
        self.assertIsNotNone(heavy)
        self.assertEqual(heavy.id, "LAUNCH_TWO_PAYLOADS")
        self.assertAlmostEqual(heavy.total_payload_mass_kg, 2.0)
        self.assertEqual(heavy.payload_ids, ["PAY_1", "PAY_2"])

    def test_get_heaviest_edge_cases_mixed_payloads(self):
        """
        Edge cases from the API:
        - null mass_kg should be treated as 0.0
        - empty payloads should be treated as 0.0
        - multiple launches on the same date_unix
        - the one with mass_kg = 5100 must be selected
        """
        docs = [
            {
                "payloads": [{"mass_kg": None, "id": "PAY_NULL_A"}],
                "date_unix": 1669852800,  # 2022-12-01 00:00:00Z
                "id": "LAUNCH_DEC01_NULL_A"
            },
            {
                "payloads": [{"mass_kg": 5100, "id": "PAY_HEAVY_5100"}],
                "date_unix": 1669852800,  # 2022-12-01
                "id": "LAUNCH_DEC01_HEAVY"
            },
            {
                "payloads": [{"mass_kg": None, "id": "PAY_NULL_B"}],
                "date_unix": 1669852800,  # 2022-12-01
                "id": "LAUNCH_DEC01_NULL_B"
            },
            {
                "payloads": [],
                "date_unix": 1669852800,  # 2022-12-01
                "id": "LAUNCH_DEC01_EMPTY_A"
            },
            {
                "payloads": [],
                "date_unix": 1669852800,  # 2022-12-01
                "id": "LAUNCH_DEC01_EMPTY_B"
            },
            {
                "payloads": [],
                "date_unix": 1670198400,  # 2022-12-05
                "id": "LAUNCH_DEC05_EMPTY"
            },
        ]

        def fake_post(url, json=None, timeout=None):
            # Return the above edge-case docs
            return DummyResp(docs)
        requests.post = fake_post

        # Full December 2022 just to be explicit; all docs are within this range
        heavy = self.client.get_heaviest_launch(start_date=date(2022, 12, 1), end_date=date(2022, 12, 31))
        self.assertIsNotNone(heavy)
        self.assertEqual(heavy.id, "LAUNCH_DEC01_HEAVY")
        self.assertAlmostEqual(heavy.total_payload_mass_kg, 5100.0)
        self.assertEqual(heavy.payload_ids, ["PAY_HEAVY_5100"])

if __name__ == "__main__":
    unittest.main()

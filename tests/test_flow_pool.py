"""Unit tests for scripts/lib/flow_pool.py (review finding B-07).

Includes a jsonschema validation test against schemas/flow_account_pool.schema.json
itself - CLAUDE.md law #1 ("Contract over prose") means this module's
output isn't done until it actually validates, not just "looks right"."""
import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from lib.flow_pool import FlowAccountPool, FlowPoolNotInitialized

try:
    import jsonschema
    HAVE_JSONSCHEMA = True
except ImportError:
    HAVE_JSONSCHEMA = False

TWO_ACCOUNTS = [
    {"account_id": "FLWACC-01", "email": "studio1@example.com"},
    {"account_id": "FLWACC-02", "email": "studio2@example.com"},
]


class TestFlowAccountPool(unittest.TestCase):
    def test_requires_real_accounts_never_invents(self):
        with tempfile.TemporaryDirectory() as td:
            pool = FlowAccountPool(Path(td))
            with self.assertRaises(ValueError):
                pool.init_new([])

    def test_next_available_account_before_init_raises(self):
        with tempfile.TemporaryDirectory() as td:
            pool = FlowAccountPool(Path(td))
            with self.assertRaises(FlowPoolNotInitialized):
                pool.next_available_account()

    def test_init_new_creates_active_accounts(self):
        with tempfile.TemporaryDirectory() as td:
            pool = FlowAccountPool(Path(td))
            data = pool.init_new(TWO_ACCOUNTS)
            self.assertEqual(len(data["accounts"]), 2)
            self.assertTrue(all(a["state"] == "ACTIVE" for a in data["accounts"]))
            self.assertEqual(data["pool_totals"]["active_accounts"], 2)

    @unittest.skipUnless(HAVE_JSONSCHEMA, "jsonschema not installed")
    def test_init_new_output_validates_against_schema(self):
        schema = json.loads((REPO_ROOT / "schemas" / "flow_account_pool.schema.json").read_text())
        with tempfile.TemporaryDirectory() as td:
            pool = FlowAccountPool(Path(td))
            data = pool.init_new(TWO_ACCOUNTS)
            jsonschema.validate(data, schema)  # raises on violation

    def test_next_available_account_picks_least_loaded(self):
        with tempfile.TemporaryDirectory() as td:
            pool = FlowAccountPool(Path(td))
            pool.init_new(TWO_ACCOUNTS)
            pool.record_usage("FLWACC-01", video_seconds=8)
            picked = pool.next_available_account()
            self.assertEqual(picked["account_id"], "FLWACC-02")

    def test_record_usage_exhausts_at_daily_cap(self):
        with tempfile.TemporaryDirectory() as td:
            pool = FlowAccountPool(Path(td))
            pool.init_new([TWO_ACCOUNTS[0]])
            for _ in range(3):
                pool.record_usage("FLWACC-01", video_seconds=5)
            self.assertIsNone(pool.next_available_account())
            data = pool._load()
            self.assertEqual(data["accounts"][0]["state"], "EXHAUSTED")
            self.assertEqual(data["accounts"][0]["videos_used_today"], 3)

    def test_record_usage_unknown_account_raises(self):
        with tempfile.TemporaryDirectory() as td:
            pool = FlowAccountPool(Path(td))
            pool.init_new(TWO_ACCOUNTS)
            with self.assertRaises(ValueError):
                pool.record_usage("FLWACC-99", video_seconds=5)

    def test_image_usage_never_exhausts_account(self):
        with tempfile.TemporaryDirectory() as td:
            pool = FlowAccountPool(Path(td))
            pool.init_new([TWO_ACCOUNTS[0]])
            for _ in range(50):
                pool.record_usage("FLWACC-01", is_image=True)
            data = pool._load()
            self.assertEqual(data["accounts"][0]["images_used_today"], 50)
            self.assertEqual(data["accounts"][0]["state"], "ACTIVE")

    def test_quarantine_removes_account_from_rotation(self):
        with tempfile.TemporaryDirectory() as td:
            pool = FlowAccountPool(Path(td))
            pool.init_new(TWO_ACCOUNTS)
            pool.quarantine("FLWACC-01", "rate limit ban observed")
            picked = pool.next_available_account()
            self.assertEqual(picked["account_id"], "FLWACC-02")

    def test_reset_if_new_day_clears_exhausted_accounts(self):
        with tempfile.TemporaryDirectory() as td:
            pool = FlowAccountPool(Path(td))
            pool.init_new([TWO_ACCOUNTS[0]])
            for _ in range(3):
                pool.record_usage("FLWACC-01", video_seconds=5)
            self.assertIsNone(pool.next_available_account())

            # Force reset_at into the past to simulate a day boundary.
            data = pool._load()
            data["accounts"][0]["reset_at"] = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
            pool._save(data)

            changed = pool.reset_if_new_day()
            self.assertTrue(changed)
            picked = pool.next_available_account()
            self.assertIsNotNone(picked)
            self.assertEqual(picked["videos_used_today"], 0)

    def test_reset_if_new_day_does_not_touch_quarantined(self):
        with tempfile.TemporaryDirectory() as td:
            pool = FlowAccountPool(Path(td))
            pool.init_new([TWO_ACCOUNTS[0]])
            pool.quarantine("FLWACC-01", "abuse pattern")
            data = pool._load()
            data["accounts"][0]["reset_at"] = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
            pool._save(data)

            pool.reset_if_new_day()
            data = pool._load()
            self.assertEqual(data["accounts"][0]["state"], "QUARANTINED")

    def test_persists_across_instances(self):
        with tempfile.TemporaryDirectory() as td:
            FlowAccountPool(Path(td)).init_new(TWO_ACCOUNTS)
            reloaded = FlowAccountPool(Path(td))
            picked = reloaded.next_available_account()
            self.assertIsNotNone(picked)


if __name__ == "__main__":
    unittest.main()

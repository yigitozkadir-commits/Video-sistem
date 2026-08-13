"""Unit tests for scripts/lib/production_ledger.py's pure/deterministic
pieces: ArtifactCache.fingerprint() and CostLedger.would_exceed_quota()
(review finding B-04)."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from lib.production_ledger import ArtifactCache, CostLedger


class TestFingerprint(unittest.TestCase):
    def test_deterministic_same_inputs_same_hash(self):
        a = ArtifactCache.fingerprint(text="hello", voice="X", model="eleven_v2")
        b = ArtifactCache.fingerprint(text="hello", voice="X", model="eleven_v2")
        self.assertEqual(a, b)

    def test_key_order_does_not_matter(self):
        a = ArtifactCache.fingerprint(text="hello", voice="X", model="eleven_v2")
        b = ArtifactCache.fingerprint(model="eleven_v2", text="hello", voice="X")
        self.assertEqual(a, b, "fingerprint must be order-independent (sort_keys=True)")

    def test_different_inputs_different_hash(self):
        a = ArtifactCache.fingerprint(text="hello", voice="X")
        b = ArtifactCache.fingerprint(text="hello world", voice="X")
        self.assertNotEqual(a, b)

    def test_sensitive_to_value_type(self):
        # json.dumps distinguishes "1" from 1 - fingerprint should too,
        # since a caller accidentally passing a stringified number for a
        # numeric input (e.g. stability="0.8" vs stability=0.8) is exactly
        # the kind of silent cache-key collision this function exists to
        # prevent.
        a = ArtifactCache.fingerprint(stability=1)
        b = ArtifactCache.fingerprint(stability="1")
        self.assertNotEqual(a, b)

    def test_returns_hex_sha256(self):
        fp = ArtifactCache.fingerprint(text="hello")
        self.assertEqual(len(fp), 64)
        int(fp, 16)  # raises ValueError if not valid hex


class TestArtifactCacheRoundtrip(unittest.TestCase):
    def test_miss_then_hit_after_put(self):
        with tempfile.TemporaryDirectory() as td:
            state_dir = Path(td) / "state"
            cache = ArtifactCache(state_dir)
            fp = ArtifactCache.fingerprint(text="hello")
            self.assertIsNone(cache.get(fp))

            artifact = Path(td) / "out.wav"
            artifact.write_bytes(b"fake-audio-bytes")
            cache.put(fp, artifact)

            # New instance re-reading the persisted index - covers the
            # actual "re-run is a no-op" guarantee (CLAUDE.md hard rule),
            # not just the in-memory dict.
            cache2 = ArtifactCache(state_dir)
            self.assertEqual(cache2.get(fp), artifact)

    def test_stale_index_entry_returns_none(self):
        with tempfile.TemporaryDirectory() as td:
            state_dir = Path(td) / "state"
            cache = ArtifactCache(state_dir)
            fp = ArtifactCache.fingerprint(text="hello")
            artifact = Path(td) / "out.wav"
            artifact.write_bytes(b"fake-audio-bytes")
            cache.put(fp, artifact)
            artifact.unlink()  # simulate the cached file having been deleted
            self.assertIsNone(cache.get(fp))


class TestWouldExceedQuota(unittest.TestCase):
    def test_no_known_cap_never_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            ledger = CostLedger(Path(td) / "state", known_quota_units={})
            self.assertFalse(ledger.would_exceed_quota("elevenlabs", 999999))

    def test_under_cap_allows(self):
        with tempfile.TemporaryDirectory() as td:
            ledger = CostLedger(Path(td) / "state", known_quota_units={"elevenlabs": 10000})
            self.assertFalse(ledger.would_exceed_quota("elevenlabs", 9999))

    def test_at_exact_cap_allows(self):
        with tempfile.TemporaryDirectory() as td:
            ledger = CostLedger(Path(td) / "state", known_quota_units={"elevenlabs": 10000})
            self.assertFalse(ledger.would_exceed_quota("elevenlabs", 10000))

    def test_over_cap_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            ledger = CostLedger(Path(td) / "state", known_quota_units={"elevenlabs": 10000})
            self.assertTrue(ledger.would_exceed_quota("elevenlabs", 10001))

    def test_accounts_for_prior_accepted_usage(self):
        with tempfile.TemporaryDirectory() as td:
            ledger = CostLedger(Path(td) / "state", known_quota_units={"elevenlabs": 10000})
            ledger.log("elevenlabs", "tts", units=6000, unit_cost=0.0, accepted=True)
            self.assertFalse(ledger.would_exceed_quota("elevenlabs", 4000))
            self.assertTrue(ledger.would_exceed_quota("elevenlabs", 4001))

    def test_rejected_calls_do_not_count_against_quota(self):
        with tempfile.TemporaryDirectory() as td:
            ledger = CostLedger(Path(td) / "state", known_quota_units={"elevenlabs": 10000})
            ledger.log("elevenlabs", "tts", units=9999, unit_cost=0.0, accepted=False)
            self.assertFalse(ledger.would_exceed_quota("elevenlabs", 9999))

    def test_providers_tracked_independently(self):
        with tempfile.TemporaryDirectory() as td:
            ledger = CostLedger(Path(td) / "state", known_quota_units={"elevenlabs": 10000, "gemini": 100})
            ledger.log("elevenlabs", "tts", units=10000, unit_cost=0.0, accepted=True)
            self.assertTrue(ledger.would_exceed_quota("elevenlabs", 1))
            self.assertFalse(ledger.would_exceed_quota("gemini", 50))

    def test_operation_prefix_keeps_tts_and_music_quota_separate(self):
        # schemas/cost_ledger.schema.json's provider enum has no distinct
        # "elevenlabs_music" value, so both narration (character units) and
        # music (second units) log under provider="elevenlabs". Without
        # operation_prefix filtering, music's seconds would inflate the
        # narration character-quota check (and vice versa) - this is the
        # cross-contamination the B-06 generate_music() wiring introduced
        # and had to guard against.
        with tempfile.TemporaryDirectory() as td:
            ledger = CostLedger(Path(td) / "state", known_quota_units={"elevenlabs": 10000})
            ledger.log("elevenlabs", "music_generate", units=9000, unit_cost=0.0, accepted=True)
            # 9000 "seconds" logged under music must not count against a
            # tts-only quota check for another 5000 characters.
            self.assertFalse(ledger.would_exceed_quota("elevenlabs", 5000, operation_prefix="tts_"))
            # but an unfiltered check still sees the combined total (the
            # pre-fix, whole-provider behavior remains available on purpose).
            self.assertTrue(ledger.would_exceed_quota("elevenlabs", 5000))

    def test_operation_prefix_matches_multiple_operations_with_same_prefix(self):
        with tempfile.TemporaryDirectory() as td:
            ledger = CostLedger(Path(td) / "state", known_quota_units={"elevenlabs": 100})
            ledger.log("elevenlabs", "tts_generate", units=40, unit_cost=0.0, accepted=True)
            ledger.log("elevenlabs", "tts_cache_hit", units=0, unit_cost=0.0, accepted=True)
            self.assertEqual(ledger.units_used("elevenlabs", operation_prefix="tts_"), 40)


if __name__ == "__main__":
    unittest.main()

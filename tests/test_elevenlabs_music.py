"""Functional (network-mocked) tests for elevenlabs_client.py's
generate_music() (review finding B-06) - exercises the actual cache-hit /
cost-ledger / NonRetryable-on-quota wiring end to end, not just syntax.
No real ElevenLabs API key or network access used: self.client.music.compose
is monkeypatched."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

os.environ.setdefault("ELEVENLABS_API_KEY", "test-key-not-real")

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

try:
    import elevenlabs  # noqa: F401
    HAVE_SDK = True
except ImportError:
    HAVE_SDK = False


@unittest.skipUnless(HAVE_SDK, "elevenlabs SDK not installed")
class TestGenerateMusic(unittest.TestCase):
    def _studio(self):
        from elevenlabs_client import ElevenLabsStudio
        studio = ElevenLabsStudio()
        studio.client = MagicMock()
        return studio

    def test_generates_and_caches(self):
        studio = self._studio()
        studio.client.music.compose.return_value = iter([b"fake-music-bytes"])

        with tempfile.TemporaryDirectory() as td:
            project_dir = Path(td) / "projects" / "PRJ-test"
            output_path = project_dir / "assets" / "audio" / "MUS-SC-001.mp3"
            result = studio.generate_music("epic steppe drums", "SC-001", output_path, duration_s=10)

            self.assertEqual(result["status"], "completed")
            self.assertTrue(output_path.exists())
            self.assertEqual(output_path.read_bytes(), b"fake-music-bytes")
            studio.client.music.compose.assert_called_once()
            kwargs = studio.client.music.compose.call_args.kwargs
            self.assertEqual(kwargs["music_length_ms"], 10000)
            self.assertTrue(kwargs["force_instrumental"])

            # cost ledger recorded under provider=elevenlabs, not a units-in-seconds
            # value that could leak into the TTS character quota (B-06 fix).
            ledger_path = project_dir / "state" / "cost_ledger.jsonl"
            rows = [json.loads(line) for line in ledger_path.read_text().splitlines()]
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["provider"], "elevenlabs")
            self.assertEqual(rows[0]["operation"], "music_generate")
            self.assertEqual(rows[0]["units"], 10)

            # second call with identical inputs must hit cache, not call the API again.
            studio.client.music.compose.reset_mock()
            result2 = studio.generate_music("epic steppe drums", "SC-001", output_path, duration_s=10)
            self.assertEqual(result2["status"], "completed_from_cache")
            studio.client.music.compose.assert_not_called()

    def test_quota_exceeded_is_nonretryable_and_logged(self):
        studio = self._studio()

        class FakeApiError(Exception):
            body = "quota_exceeded: music generation limit reached"

        studio.client.music.compose.side_effect = FakeApiError("quota_exceeded")

        with tempfile.TemporaryDirectory() as td:
            project_dir = Path(td) / "projects" / "PRJ-test"
            output_path = project_dir / "assets" / "audio" / "MUS-SC-002.mp3"
            with self.assertRaises(Exception):
                studio.generate_music("tense strings", "SC-002", output_path, duration_s=8)

            # must not have retried (NonRetryable short-circuits) - compose called exactly once.
            self.assertEqual(studio.client.music.compose.call_count, 1)

            ledger_rows = [
                json.loads(line)
                for line in (project_dir / "state" / "cost_ledger.jsonl").read_text().splitlines()
            ]
            self.assertEqual(ledger_rows[-1]["accepted"], False)

            error_rows = [
                json.loads(line)
                for line in (project_dir / "state" / "errors.jsonl").read_text().splitlines()
            ]
            self.assertEqual(error_rows[-1]["code"], "E-BUD-001")
            self.assertFalse(output_path.exists())


if __name__ == "__main__":
    unittest.main()

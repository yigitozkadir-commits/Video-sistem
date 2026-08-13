"""Unit tests for scripts/generate_captions.py (review finding B-05).

transcribe_words() (the actual faster-whisper call) is mocked throughout -
these tests exercise the fingerprinting/no-op/caching orchestration and
the schema-shape of the output, not whether faster-whisper itself works.
A separate test forces FASTER_WHISPER_AVAILABLE=False to verify the
missing-dependency error path deterministically, regardless of whether
faster-whisper happens to be installed in the environment running the
suite."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
import generate_captions as gc  # noqa: E402

try:
    import jsonschema
    HAVE_JSONSCHEMA = True
except ImportError:
    HAVE_JSONSCHEMA = False

FAKE_CAPTIONS = [
    {"text": "Merhaba", "startMs": 0, "endMs": 400, "timestampMs": None, "confidence": 0.98},
    {"text": " dünya", "startMs": 400, "endMs": 900, "timestampMs": None, "confidence": 0.95},
]


class TestGenerateCaptions(unittest.TestCase):
    def _fake_audio(self, td: str) -> Path:
        audio = Path(td) / "NAR-SC-001.wav"
        audio.write_bytes(b"fake-wav-bytes-not-real-audio")
        return audio

    def test_missing_audio_file_raises(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(FileNotFoundError):
                gc.generate_captions("SC-001", Path(td) / "missing.wav", Path(td) / "out.json")

    def test_writes_schema_shaped_output(self):
        with tempfile.TemporaryDirectory() as td:
            audio = self._fake_audio(td)
            output = Path(td) / "SC-001.json"
            with patch.object(gc, "transcribe_words", return_value=(FAKE_CAPTIONS, "tr")):
                data = gc.generate_captions("SC-001", audio, output, model_name="base", language="tr")

            self.assertTrue(output.exists())
            self.assertEqual(data["scene_id"], "SC-001")
            self.assertEqual(data["model"], "faster-whisper-base")
            self.assertEqual(data["language"], "tr")
            self.assertEqual(data["captions"], FAKE_CAPTIONS)
            self.assertIn("inputs_fingerprint", data)
            self.assertEqual(json.loads(output.read_text()), data)

    def test_unchanged_inputs_is_a_noop_does_not_retranscribe(self):
        with tempfile.TemporaryDirectory() as td:
            audio = self._fake_audio(td)
            output = Path(td) / "SC-001.json"
            with patch.object(gc, "transcribe_words", return_value=(FAKE_CAPTIONS, "tr")) as mock_tw:
                gc.generate_captions("SC-001", audio, output, model_name="base", language="tr")
                self.assertEqual(mock_tw.call_count, 1)

                # same audio, same model/language - should skip the (expensive) transcribe call.
                gc.generate_captions("SC-001", audio, output, model_name="base", language="tr")
                self.assertEqual(mock_tw.call_count, 1, "re-running with unchanged inputs must be a no-op")

    def test_changed_audio_retranscribes(self):
        with tempfile.TemporaryDirectory() as td:
            audio = self._fake_audio(td)
            output = Path(td) / "SC-001.json"
            with patch.object(gc, "transcribe_words", return_value=(FAKE_CAPTIONS, "tr")) as mock_tw:
                gc.generate_captions("SC-001", audio, output, model_name="base", language="tr")
                audio.write_bytes(b"different-audio-bytes-entirely")
                gc.generate_captions("SC-001", audio, output, model_name="base", language="tr")
                self.assertEqual(mock_tw.call_count, 2)

    def test_different_model_retranscribes(self):
        with tempfile.TemporaryDirectory() as td:
            audio = self._fake_audio(td)
            output = Path(td) / "SC-001.json"
            with patch.object(gc, "transcribe_words", return_value=(FAKE_CAPTIONS, "tr")) as mock_tw:
                gc.generate_captions("SC-001", audio, output, model_name="base", language="tr")
                gc.generate_captions("SC-001", audio, output, model_name="small", language="tr")
                self.assertEqual(mock_tw.call_count, 2)

    def test_force_retranscribes_even_if_unchanged(self):
        with tempfile.TemporaryDirectory() as td:
            audio = self._fake_audio(td)
            output = Path(td) / "SC-001.json"
            with patch.object(gc, "transcribe_words", return_value=(FAKE_CAPTIONS, "tr")) as mock_tw:
                gc.generate_captions("SC-001", audio, output, model_name="base", language="tr")
                gc.generate_captions("SC-001", audio, output, model_name="base", language="tr", force=True)
                self.assertEqual(mock_tw.call_count, 2)

    def test_missing_dependency_raises_actionable_error(self):
        with patch.object(gc, "FASTER_WHISPER_AVAILABLE", False):
            with self.assertRaises(gc.FasterWhisperNotInstalled) as ctx:
                gc.transcribe_words(Path("irrelevant.wav"), "base", "tr")
            self.assertIn("pip install faster-whisper", str(ctx.exception))

    @unittest.skipUnless(HAVE_JSONSCHEMA, "jsonschema not installed")
    def test_output_validates_against_schema(self):
        schema = json.loads((REPO_ROOT / "schemas" / "caption_track.schema.json").read_text())
        with tempfile.TemporaryDirectory() as td:
            audio = self._fake_audio(td)
            output = Path(td) / "SC-001.json"
            with patch.object(gc, "transcribe_words", return_value=(FAKE_CAPTIONS, "tr")):
                data = gc.generate_captions("SC-001", audio, output, model_name="base", language="tr")
            jsonschema.validate(data, schema)

    def test_cli_smoke(self):
        with tempfile.TemporaryDirectory() as td:
            audio = self._fake_audio(td)
            output = Path(td) / "out" / "SC-001.json"
            with patch.object(gc, "transcribe_words", return_value=(FAKE_CAPTIONS, "tr")):
                gc.main(["SC-001", str(audio), str(output)])
            self.assertTrue(output.exists())


if __name__ == "__main__":
    unittest.main()

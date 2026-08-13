"""Unit tests for scripts/piper_client.py. Piper is not installed in this
environment (see piper_client.py's module docstring) - subprocess.run is
mocked throughout, matching this repo's convention for external calls that
can't run in-sandbox (tests/test_find_reference_images.py's provider
mocking)."""
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import piper_client as pc  # noqa: E402


def _ok_result(stdout="", stderr=""):
    r = MagicMock()
    r.returncode = 0
    r.stdout = stdout
    r.stderr = stderr
    return r


class TestPiperClientInit(unittest.TestCase):
    def test_missing_model_path_raises(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                pc.PiperClient()

    def test_model_name_derived_from_model_path_stem(self):
        with patch.dict(os.environ, {"PIPER_MODEL_PATH": "/models/en_US-lessac-medium.onnx"}, clear=True):
            client = pc.PiperClient()
        self.assertEqual(client.model_name, "piper:en_US-lessac-medium")

    def test_quality_gate_is_always_draft_only(self):
        with patch.dict(os.environ, {"PIPER_MODEL_PATH": "/models/x.onnx"}, clear=True):
            client = pc.PiperClient()
        self.assertEqual(client.quality_gate, "draft_only")


class TestPiperTextToSpeech(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.output_path = Path(self._tmpdir.name) / "projects" / "PRJ-test" / "assets" / "audio" / "NAR-SC-001.wav"
        self.env_patch = patch.dict(os.environ, {"PIPER_MODEL_PATH": "/models/en_US-lessac-medium.onnx"}, clear=True)
        self.env_patch.start()
        self.addCleanup(self.env_patch.stop)
        self.client = pc.PiperClient()

    def _write_fake_wav(self, *a, **kw):
        # subprocess.run is mocked, so the real piper binary never writes
        # output_path - simulate that side effect so ArtifactCache.put()'s
        # sha256 read succeeds, matching what a real successful call does.
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_path.write_bytes(b"fake-wav-bytes")
        return _ok_result()

    def test_successful_generation_calls_piper_and_returns_metadata(self):
        with patch("piper_client.subprocess.run", side_effect=self._write_fake_wav) as mock_run:
            result = self.client.text_to_speech("Merhaba dünya", "SC-001", self.output_path)

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["quality_gate"], "draft_only")
        self.assertEqual(result["scene_id"], "SC-001")
        cmd = mock_run.call_args.args[0]
        self.assertIn("--model", cmd)
        self.assertIn("/models/en_US-lessac-medium.onnx", cmd)
        self.assertIn("--output_file", cmd)
        self.assertEqual(mock_run.call_args.kwargs["input"], "Merhaba dünya")

    def test_nonzero_exit_raises_runtime_error(self):
        bad_result = MagicMock(returncode=1, stdout="", stderr="model not found")
        with patch("piper_client.subprocess.run", return_value=bad_result):
            with self.assertRaises(RuntimeError) as ctx:
                self.client.text_to_speech("text", "SC-001", self.output_path)
        self.assertIn("model not found", str(ctx.exception))

    def test_cache_hit_skips_subprocess(self):
        with patch("piper_client.subprocess.run", side_effect=self._write_fake_wav) as mock_run:
            self.client.text_to_speech("same text", "SC-001", self.output_path)
        self.assertEqual(mock_run.call_count, 1)

        with patch("piper_client.subprocess.run", side_effect=self._write_fake_wav) as mock_run2:
            result = self.client.text_to_speech("same text", "SC-001", self.output_path)
        mock_run2.assert_not_called()
        self.assertEqual(result["status"], "completed_from_cache")

    def test_different_text_is_not_a_cache_hit(self):
        with patch("piper_client.subprocess.run", side_effect=self._write_fake_wav):
            self.client.text_to_speech("text one", "SC-001", self.output_path)
        with patch("piper_client.subprocess.run", side_effect=self._write_fake_wav) as mock_run2:
            self.client.text_to_speech("text two", "SC-001", self.output_path)
        mock_run2.assert_called_once()

    def test_speed_other_than_one_passes_inverse_length_scale(self):
        with patch("piper_client.subprocess.run", side_effect=self._write_fake_wav) as mock_run:
            self.client.text_to_speech("text", "SC-001", self.output_path, speed=2.0)
        cmd = mock_run.call_args.args[0]
        self.assertIn("--length_scale", cmd)
        idx = cmd.index("--length_scale")
        self.assertAlmostEqual(float(cmd[idx + 1]), 0.5)

    def test_extra_elevenlabs_only_kwargs_are_ignored_not_errors(self):
        with patch("piper_client.subprocess.run", side_effect=self._write_fake_wav):
            result = self.client.text_to_speech(
                "text", "SC-001", self.output_path, stability=0.8, similarity=0.9, style=0.2,
            )
        self.assertEqual(result["status"], "completed")


if __name__ == "__main__":
    unittest.main()

"""Unit tests for scripts/lib/tts_providers.py's select_tts_provider() -
the fallback-selection logic between ElevenLabs (default) and Piper
(draft-only, only when narration.fallback.enabled is true in
studio.config.json AND ElevenLabs itself failed to initialize)."""
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import lib.tts_providers as tp  # noqa: E402


class TestSelectTtsProvider(unittest.TestCase):
    def test_elevenlabs_available_returns_elevenlabs_no_fallback_check(self):
        fake_studio = MagicMock()
        fake_module = MagicMock()
        fake_module.ElevenLabsStudio = MagicMock(return_value=fake_studio)
        with patch.dict(sys.modules, {"elevenlabs_client": fake_module}):
            with patch.object(tp, "_narration_fallback_config") as mock_cfg:
                result = tp.select_tts_provider()
        self.assertIs(result, fake_studio)
        mock_cfg.assert_not_called()

    def test_elevenlabs_fails_fallback_disabled_reraises(self):
        fake_module = MagicMock()
        fake_module.ElevenLabsStudio = MagicMock(side_effect=ValueError("ELEVENLABS_API_KEY not set"))
        with patch.dict(sys.modules, {"elevenlabs_client": fake_module}):
            with patch.object(tp, "_narration_fallback_config", return_value={"enabled": False}):
                with self.assertRaises(ValueError):
                    tp.select_tts_provider()

    def test_elevenlabs_fails_fallback_enabled_returns_piper(self):
        fake_elevenlabs_module = MagicMock()
        fake_elevenlabs_module.ElevenLabsStudio = MagicMock(side_effect=ValueError("ELEVENLABS_API_KEY not set"))
        fake_piper_instance = MagicMock()
        fake_piper_module = MagicMock()
        fake_piper_module.PiperClient = MagicMock(return_value=fake_piper_instance)

        with patch.dict(sys.modules, {"elevenlabs_client": fake_elevenlabs_module, "piper_client": fake_piper_module}):
            with patch.object(tp, "_narration_fallback_config", return_value={"enabled": True}):
                result = tp.select_tts_provider(reason="quota exhausted mid-batch")

        self.assertIs(result, fake_piper_instance)

    def test_no_config_file_means_fallback_disabled_by_default(self):
        with patch.object(tp, "_CONFIG_PATH") as mock_path:
            mock_path.exists.return_value = False
            cfg = tp._narration_fallback_config()
        self.assertEqual(cfg, {})


if __name__ == "__main__":
    unittest.main()

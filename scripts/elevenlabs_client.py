#!/usr/bin/env python3
"""
ElevenLabs Integration for AI Audiobook Studio
Reads API credentials from environment variables
"""

import os
import json
import sys
import time
from pathlib import Path
from typing import Optional, Dict, List
import logging

sys.path.insert(0, str(Path(__file__).parent))
from lib.production_ledger import ArtifactCache, CostLedger  # noqa: E402
from lib.retry import with_retry, NonRetryable  # noqa: E402
from lib.feature_flags import is_enabled  # noqa: E402
from lib.errors import log_error  # noqa: E402

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ElevenLabs free-tier default; overridable per key via env if a paid plan is in use.
ELEVENLABS_FREE_TIER_CHAR_QUOTA = int(os.getenv("ELEVENLABS_QUOTA_CHARS", "10000"))


def _project_state_dir(output_path: Path) -> Path:
    """projects/<id>/assets/audio/x.wav -> projects/<id>/state/"""
    parts = output_path.resolve().parts
    if "projects" in parts and "assets" in parts:
        proj_idx = parts.index("projects")
        project_root = Path(*parts[: proj_idx + 2])
        return project_root / "state"
    return output_path.parent.parent / "state"

try:
    from elevenlabs.client import ElevenLabs
    from elevenlabs import VoiceSettings
    ELEVENLABS_AVAILABLE = True
except ImportError:
    ELEVENLABS_AVAILABLE = False
    logger.warning("ElevenLabs SDK not installed. Run: pip install elevenlabs")


class ElevenLabsStudio:
    """ElevenLabs integration for the studio"""

    def __init__(self):
        """Initialize with environment variables"""

        if not ELEVENLABS_AVAILABLE:
            raise ImportError("ElevenLabs SDK required. Install: pip install elevenlabs")

        # Load from environment
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        if not self.api_key:
            raise ValueError("ELEVENLABS_API_KEY not set in environment")

        self.voice_id = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")  # Default female voice
        self.model_id = os.getenv("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2")

        # Voice parameters from env or defaults
        self.stability = float(os.getenv("ELEVENLABS_STABILITY", "0.80"))
        self.similarity = float(os.getenv("ELEVENLABS_SIMILARITY", "0.90"))
        self.style = float(os.getenv("ELEVENLABS_STYLE", "0.28"))

        # Initialize client
        self.client = ElevenLabs(api_key=self.api_key)
        logger.info(f"✓ ElevenLabs initialized: {self.model_id}")

    def text_to_speech(
        self,
        text: str,
        scene_id: str,
        output_path: Path,
        stability: Optional[float] = None,
        similarity: Optional[float] = None,
        style: Optional[float] = None,
        speed: float = 1.0
    ) -> Dict:
        """
        Generate speech from text

        Args:
            text: Turkish narration text
            scene_id: Scene identifier (SC-001, etc)
            output_path: Where to save WAV file
            stability: Voice stability (0.0-1.0)
            similarity: Voice similarity (0.0-1.0)
            style: Delivery style (0.0-1.0)
            speed: Speech rate (0.5-2.0)

        Returns:
            Metadata dict with duration, timing map, etc
        """

        # Use provided params or defaults
        stab = stability or self.stability
        sim = similarity or self.similarity
        sty = style or self.style

        state_dir = _project_state_dir(output_path)
        cache = ArtifactCache(state_dir)
        ledger = CostLedger(state_dir, known_quota_units={"elevenlabs": ELEVENLABS_FREE_TIER_CHAR_QUOTA})
        fp = ArtifactCache.fingerprint(
            text=text, voice_id=self.voice_id, model_id=self.model_id,
            stability=stab, similarity=sim, style=sty,
        )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        skip_cache = is_enabled("skip_cache", default=False)
        if skip_cache:
            logger.info("  FLAG_SKIP_CACHE set - forcing regeneration even if cached")
        if not skip_cache and cache.reuse(fp, output_path):
            logger.info(f"✓ Cache hit, reused existing audio: {scene_id}")
            ledger.log("elevenlabs", "tts_cache_hit", units=0, unit_cost=0, accepted=True)
            return {
                "scene_id": scene_id, "file": str(output_path), "model": self.model_id,
                "voice_id": self.voice_id, "stability": stab, "similarity": sim,
                "style": sty, "speed": speed, "status": "completed_from_cache",
            }

        char_count = len(text)
        if ledger.would_exceed_quota("elevenlabs", char_count):
            used = ledger.units_used("elevenlabs")
            msg = (
                f"Skipping API call: {used:.0f}/{ELEVENLABS_FREE_TIER_CHAR_QUOTA} chars already "
                f"used this key, request needs {char_count} more. Swap the API key before retrying "
                f"rather than burning the request on a call that will 401."
            )
            log_error(state_dir, code="E-BUD-001", message=msg, retryable=False,
                      escalate_to="human", suggested_strategy="swap ELEVENLABS_API_KEY, then retry")
            raise RuntimeError(msg)

        logger.info(f"Generating narration: {scene_id}")
        logger.info(f"  Text: {text[:100]}...")
        logger.info(f"  Params: stability={stab}, similarity={sim}, style={sty}")

        def _call_api():
            try:
                audio_generator = self.client.text_to_speech.convert(
                    text=text,
                    voice_id=self.voice_id,
                    model_id=self.model_id,
                    voice_settings=VoiceSettings(
                        stability=stab,
                        similarity_boost=sim,
                        style=sty,
                        use_speaker_boost=True
                    )
                )
                with open(output_path, "wb") as f:
                    for chunk in audio_generator:
                        f.write(chunk)
            except Exception as e:
                body = str(getattr(e, "body", "")) + str(e)
                if "quota_exceeded" in body or "payment_required" in body:
                    # Not transient - retrying burns another request against
                    # the same wall. Fail fast per CLAUDE.md law #6.
                    raise NonRetryable(e) from e
                raise

        def _log_retry(attempt: int, exc: Exception) -> None:
            logger.warning(f"  transient failure (attempt {attempt}), retrying: {exc}")

        call_started = time.monotonic()
        try:
            with_retry(
                _call_api, category="generation", on_retry=_log_retry,
                error_context={
                    "project_state_dir": state_dir,
                    "code": "E-GEN-001",  # attempts exhausted, still-transient (network/5xx)
                    "nonretryable_code": "E-BUD-001",  # NonRetryable path: _call_api raises it only for quota_exceeded/payment_required
                    "escalate_to": "human",
                    "suggested_strategy": "swap ELEVENLABS_API_KEY, then retry this scene",
                },
            )
            duration_s = time.monotonic() - call_started
            logger.info(f"✓ Saved: {output_path} ({duration_s:.1f}s)")
            cache.put(fp, output_path, scene_id=scene_id, char_count=char_count)
            ledger.log("elevenlabs", "tts_generate", units=char_count, unit_cost=1,
                       accepted=True, duration_s=duration_s)

            # Get duration info (would need ffprobe for real)
            metadata = {
                "scene_id": scene_id,
                "file": str(output_path),
                "model": self.model_id,
                "voice_id": self.voice_id,
                "stability": stab,
                "similarity": sim,
                "style": sty,
                "speed": speed,
                "status": "completed"
            }

            return metadata

        except Exception as e:
            logger.error(f"✗ Generation failed: {e}")
            ledger.log("elevenlabs", "tts_generate", units=char_count, unit_cost=1,
                       accepted=False, duration_s=time.monotonic() - call_started)
            raise

    def generate_music(
        self,
        prompt: str,
        scene_id: str,
        output_path: Path,
        duration_s: int = 12
    ) -> Dict:
        """
        Generate music for a scene (if Music API available)

        Args:
            prompt: Music description/mood
            scene_id: Scene identifier
            output_path: Where to save WAV
            duration_s: Duration in seconds

        Returns:
            Metadata dict
        """

        logger.warning(f"Music generation requires ElevenLabs Music API")
        logger.info(f"Prompt: {prompt}")

        # This would call the music API if available
        # For now, return metadata structure
        metadata = {
            "scene_id": scene_id,
            "file": str(output_path),
            "type": "music",
            "prompt": prompt,
            "duration_s": duration_s,
            "status": "pending_manual_generation",
            "note": "Use ElevenLabs web interface for music generation"
        }

        logger.info(f"→ Please generate music manually in ElevenLabs dashboard")
        logger.info(f"  Prompt: {prompt}")
        logger.info(f"  Duration: {duration_s}s")

        return metadata

    def list_voices(self) -> List[Dict]:
        """Get available voices"""
        try:
            response = self.client.voices.get_all()
            voices = response.voices if hasattr(response, 'voices') else response
            return [{"id": v.voice_id, "name": v.name} for v in voices]
        except Exception as e:
            logger.error(f"Could not list voices: {e}")
            return []

    def set_voice(self, voice_id: str):
        """Switch to different voice"""
        self.voice_id = voice_id
        logger.info(f"✓ Voice set to: {voice_id}")


def main():
    """CLI for testing"""

    try:
        studio = ElevenLabsStudio()

        # Test: list available voices
        print("\n📢 Available Voices:")
        for voice in studio.list_voices()[:5]:
            print(f"  {voice['id']}: {voice['name']}")

        # Test: generate sample narration
        sample_text = "Selam dünya. Bu bir test sesidir."
        output = Path("/tmp/test_narration.wav")

        print(f"\n🎤 Generating test narration...")
        metadata = studio.text_to_speech(
            text=sample_text,
            scene_id="SC-TEST",
            output_path=output
        )
        print(f"✓ Generated: {json.dumps(metadata, indent=2)}")

    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

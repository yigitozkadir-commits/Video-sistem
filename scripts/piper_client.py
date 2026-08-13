#!/usr/bin/env python3
"""
Piper TTS client - the local, free, no-network fallback for when ElevenLabs
is unavailable (missing API key, quota exhausted). See scripts/lib/
tts_providers.py's module docstring for why this exists.

quality_gate = "draft_only" is not a suggestion: Piper's output is a robotic
local voice, fine for previewing pacing/timing while iterating on a scene,
never acceptable as a delivered master. Nothing in this file marks a Piper
take as final - that gate is enforced by whatever writes the master export
checking quality_gate before accepting a take (CLAUDE.md law #4).

Requires the piper binary on PATH (or PIPER_BINARY) and a downloaded .onnx
voice model (PIPER_MODEL_PATH) - see https://github.com/OHF-Voice/piper1-gpl
for model downloads. Not installed in this environment; this client is
correct-by-construction against Piper's documented CLI contract
(--model, --output_file, text on stdin) but has not been run against a
real binary here - unit tests mock subprocess.run, matching this repo's
existing convention for untestable-in-sandbox external calls (see
tests/test_find_reference_images.py's provider mocking).
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Optional

sys.path.insert(0, str(Path(__file__).parent))
from lib.production_ledger import ArtifactCache, CostLedger  # noqa: E402
from lib.tts_providers import _project_state_dir  # noqa: E402


class PiperClient:
    """Local Piper TTS - draft-quality fallback, never a master source."""

    quality_gate = "draft_only"

    def __init__(self):
        self.binary = os.getenv("PIPER_BINARY", "piper")
        self.model_path = os.getenv("PIPER_MODEL_PATH")
        if not self.model_path:
            raise ValueError(
                "PIPER_MODEL_PATH not set in environment - point it at a "
                "downloaded .onnx voice model (see "
                "https://github.com/OHF-Voice/piper1-gpl for voices)"
            )
        self.speaker_id = os.getenv("PIPER_SPEAKER_ID")  # optional, multi-speaker models
        self.model_name = f"piper:{Path(self.model_path).stem}"

    def text_to_speech(
        self,
        text: str,
        scene_id: str,
        output_path: Path,
        speed: float = 1.0,
        **kwargs,
    ) -> Dict:
        """Same call shape as ElevenLabsStudio.text_to_speech() (positional
        text/scene_id/output_path, metadata dict back) so callers can hold
        either behind scripts/lib/tts_providers.py's TTSProvider shape.
        Extra ElevenLabs-only kwargs (stability/similarity/style) are
        accepted and ignored - Piper has no equivalent controls."""
        state_dir = _project_state_dir(output_path)
        cache = ArtifactCache(state_dir, index_name="piper_audio_cache_index.json")
        ledger = CostLedger(state_dir)
        fp = ArtifactCache.fingerprint(
            text=text, model=self.model_name, speaker_id=self.speaker_id, speed=speed,
        )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        if cache.reuse(fp, output_path):
            ledger.log("other", "piper_tts_cache_hit", units=0, unit_cost=0, accepted=True, scene_id=scene_id)
            return {
                "scene_id": scene_id, "file": str(output_path), "model": self.model_name,
                "speed": speed, "quality_gate": self.quality_gate, "status": "completed_from_cache",
            }

        cmd = [self.binary, "--model", self.model_path, "--output_file", str(output_path)]
        if self.speaker_id:
            cmd += ["--speaker", self.speaker_id]
        if speed != 1.0:
            # Piper's CLI takes a length_scale multiplier where LOWER is
            # FASTER (it scales phoneme duration) - inverse of "speed".
            cmd += ["--length_scale", str(1.0 / speed)]

        call_started = time.monotonic()
        result = subprocess.run(cmd, input=text, capture_output=True, text=True)
        duration_s = time.monotonic() - call_started

        if result.returncode != 0:
            ledger.log("other", "piper_tts_generate", units=len(text), unit_cost=0,
                       accepted=False, duration_s=duration_s, scene_id=scene_id)
            raise RuntimeError(f"piper exited {result.returncode}: {result.stderr.strip()}")

        cache.put(fp, output_path, scene_id=scene_id, char_count=len(text))
        ledger.log("other", "piper_tts_generate", units=len(text), unit_cost=0,
                   accepted=True, duration_s=duration_s, scene_id=scene_id)

        return {
            "scene_id": scene_id, "file": str(output_path), "model": self.model_name,
            "speed": speed, "quality_gate": self.quality_gate, "status": "completed",
        }


def main():
    """CLI for testing (mirrors elevenlabs_client.py's own __main__ block)."""
    try:
        client = PiperClient()
        sample_text = "Selam dünya. Bu bir test sesidir."
        output = Path("/tmp/test_piper_narration.wav")
        print(f"Generating test narration via {client.model_name}...")
        metadata = client.text_to_speech(text=sample_text, scene_id="SC-TEST", output_path=output)
        print(f"Generated: {metadata}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

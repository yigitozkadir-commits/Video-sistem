#!/usr/bin/env python3
"""
Generates NAR-<scene_id>.wav for every scene in PRJ-baskurtlar-arastirma via
ElevenLabsStudio.text_to_speech() (cache/retry/cost-ledger already built
into scripts/elevenlabs_client.py - this script just drives it per scene).

Voice: George (JBFqnCBsd6RMkjVDRZzb) - "Warm, Captivating Storyteller",
chosen to match this project's narrative_structure ("storytelling", see
CFP-0001/CFP-0002 and TPL-baskurtlar-hybrid) and the "Sessiz Rehber" warm-
but-authoritative persona, rather than reusing "Jessica" (bright/playful,
picked for the children's fairytale project - wrong register here).
Stability/style come from templates/TPL-baskurtlar-hybrid.json's
audio.narrator block (0.55 / 0.25); similarity uses the existing env
default since the template doesn't override it.

Every scene gets its own narration regardless of visual_decision (reuse
only applies to the VISUAL, never to narration text).

Usage:
    python3 scripts/generate_baskurtlar_narration.py
"""
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
import json  # noqa: E402
from elevenlabs_client import ElevenLabsStudio  # noqa: E402

PROJECT_DIR = REPO_ROOT / "projects" / "PRJ-baskurtlar-arastirma"
VOICE_ID = "JBFqnCBsd6RMkjVDRZzb"  # George - Warm, Captivating Storyteller
STABILITY = 0.55
STYLE = 0.25


def main() -> None:
    studio = ElevenLabsStudio()
    studio.set_voice(VOICE_ID)

    scene_paths = sorted((PROJECT_DIR / "scenes").glob("SC-*.json"))
    done, failed = [], []
    for p in scene_paths:
        scene = json.loads(p.read_text())
        sid = scene["scene_id"]
        text = scene["source_text"]
        out_path = PROJECT_DIR / "assets" / "audio" / f"NAR-{sid}.wav"
        try:
            meta = studio.text_to_speech(
                text=text, scene_id=sid, output_path=out_path,
                stability=STABILITY, style=STYLE,
            )
            print(f"{sid}: {meta['status']} -> {out_path.relative_to(REPO_ROOT)}")
            done.append(sid)
        except Exception as e:
            print(f"{sid}: FAILED - {e}")
            failed.append(sid)
            break  # stop on first failure (likely quota) rather than burning further attempts

    print()
    print(f"Done: {len(done)}/{len(scene_paths)}")
    if failed:
        print(f"Stopped at: {failed[0]} - remaining scenes not attempted this run")


if __name__ == "__main__":
    main()

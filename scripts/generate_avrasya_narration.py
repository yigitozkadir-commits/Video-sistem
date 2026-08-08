#!/usr/bin/env python3
"""
Generates NAR-<scene_id>.wav for every scene in PRJ-avrasya-bozkir-kusagi via
ElevenLabsStudio.text_to_speech() - same driver as
scripts/generate_baskurtlar_narration.py, different voice/register.

Voice: Daniel - "Steady Broadcaster" (onwK4e9ZLuTAKqWW03F9). Chosen over the
.env default (Jessica, bright/playful - picked for the children's fairytale
project) and over Başkurtlar's George ("warm, captivating storyteller")
because TPL-archaeological-documentary.json's audio.narrator block calls for
a restrained, evidence-presenting register (stability=0.7, style=0.05,
wpm=115) - the opposite of a warm storyteller voice. First attempt used
ElevenLabs' "Rachel" (a library voice, not in this account's voice list) and
402'd with "Free users cannot use library voices via the API" - list_voices()
against this account's own premade set returned Daniel as the closest match
to "steady, evidence-presenting broadcaster" among the free-tier-usable
options (Sarah/River/Matilda were the other reasonable candidates).

Also fixed en route: this container has a stale, invalid ELEVENLABS_API_KEY
(not sk_-prefixed) already exported in the shell environment, silently
shadowing .env under load_dotenv()'s default no-override behavior - hence
load_dotenv(override=True) below.

Every scene gets its own narration regardless of visual_decision (reuse
only applies to the VISUAL, never to narration text).

Usage:
    python3 scripts/generate_avrasya_narration.py
"""
import sys
from pathlib import Path

from dotenv import load_dotenv
# override=True: this container has a stale, invalid ELEVENLABS_API_KEY (not
# sk_-prefixed, an old key ID) already exported in the shell environment,
# which silently shadows .env under load_dotenv()'s default no-override
# behavior - confirmed via `env | grep -i eleven` 2026-08-08.
load_dotenv(override=True)

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
import json  # noqa: E402
from elevenlabs_client import ElevenLabsStudio  # noqa: E402

PROJECT_DIR = REPO_ROOT / "projects" / "PRJ-avrasya-bozkir-kusagi"
VOICE_ID = "onwK4e9ZLuTAKqWW03F9"  # Daniel - Steady Broadcaster
STABILITY = 0.7
STYLE = 0.05


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

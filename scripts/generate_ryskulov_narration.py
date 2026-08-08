#!/usr/bin/env python3
"""
Generates NAR-<scene_id>.wav for every scene in PRJ-ryskulov-mektubu via
ElevenLabsStudio.text_to_speech() - same driver as
scripts/generate_avrasya_narration.py.

Voice: Adam - "Dominant, Firm" (pNInz6obpgDQGcFmaJgB). User asked for a
darker, more dramatic tone than the restrained/measured registers used so
far (Avrasya's Daniel "Steady Broadcaster", Başkurtlar's George "Warm
Storyteller") - Adam's low, firm register fits a grave historical subject
(the letter warning Stalin of the Kazakh famine) without tipping into
"Fierce Warrior" (Harry) overacting.

Delivery is tuned more expressive than Avrasya's restrained-documentary
defaults (stability=0.7, style=0.05): stability=0.45, style=0.35 here -
lower stability allows more natural variation/weight in delivery, higher
style pushes ElevenLabs toward a more emotionally engaged read. This is a
TTS delivery-parameter choice, not a rewrite of source_text - the
narration wording stays exactly as scaffolded from the cited research
report (rewriting for "drama" would risk embellishing beyond the source,
against this project's own numeric/citation rigor).

Total narration need (~11,308 chars) exceeds a single free-tier 10,000-char
key, so this is designed to run across two keys via the cache: run once
per key (swap ELEVENLABS_API_KEY in .env between runs), already-completed
scenes hit the ArtifactCache and are skipped for free.

Every scene gets its own narration regardless of visual_decision (reuse
only applies to the VISUAL, never to narration text).

Usage:
    python3 scripts/generate_ryskulov_narration.py
"""
import sys
from pathlib import Path

from dotenv import load_dotenv
# override=True: this container has a stale, invalid ELEVENLABS_API_KEY
# (not sk_-prefixed) already exported in the shell environment, silently
# shadowing .env under load_dotenv()'s default no-override behavior -
# same fix as generate_avrasya_narration.py.
load_dotenv(override=True)

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
import json  # noqa: E402
from elevenlabs_client import ElevenLabsStudio  # noqa: E402

PROJECT_DIR = REPO_ROOT / "projects" / "PRJ-ryskulov-mektubu"
VOICE_ID = "pNInz6obpgDQGcFmaJgB"  # Adam - Dominant, Firm
STABILITY = 0.45
STYLE = 0.35


def main() -> None:
    studio = ElevenLabsStudio()
    studio.set_voice(VOICE_ID)

    scene_paths = sorted((PROJECT_DIR / "scenes").glob("SC-*.json"))
    done, failed = [], []
    for p in scene_paths:
        scene = json.loads(p.read_text())
        sid = scene["scene_id"]
        text = scene["source_text"]
        if not text:
            print(f"{sid}: skip (no source_text)")
            continue
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

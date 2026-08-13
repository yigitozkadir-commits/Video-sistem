#!/usr/bin/env python3
"""
Mandatory gate before any full Remotion render (CLAUDE.md law - see
"Pre-render checklist"). Catches, cheaply and BEFORE a 45-60 minute full
render, the two defect patterns that forced repeat full-renders of the
same Başkurtlar video this session:

1. VIDEO LOOP RATIO. A scene's video-type visual slot repeats the source
   clip via `loop`; if the slot is much longer than the clip, it visibly
   stutter-loops (found retroactively: SC-001 looped its 6.016s clip
   13.7x across an 82s slot - only noticed by a human watching the
   finished render). This check recomputes each video scene's slot
   duration from the CURRENT scenesData.ts and flags any clip repeating
   more than LOOP_RATIO_THRESHOLD times, before rendering.

2. LONG COMPOUND NUMBERS IN NARRATION. ElevenLabs has been observed to
   garble long compound Turkish numbers (e.g. "bir milyon beş yüz seksen
   dört bin beş yüz elli dörttü") while nearby simpler numbers in the same
   sentence render fine - not caught by a plain digit-regex scan since no
   raw digits are present, only found via manually transcribing the
   finished audio with faster-whisper after a human flagged it by ear.
   This check flags any long spelled-out number run for a mandatory
   Whisper listen-check before render, rather than after.

This does not replace scripts/validate.py (schema conformance) or
scripts/plan_scene_count.py (Module 22 density targets) - run those too.
This script is specific to remotion_baskurtlar's architecture (video hero
scenes + still inserts via generate_baskurtlar_scenes_data.py); a future
project with a different Remotion architecture needs its own equivalent
script, per the same law.

Usage:
    python3 scripts/pre_render_checklist.py
Exit code 0 = clean, 1 = findings need review before rendering (does not
block, just refuses to claim "all clear" - CLAUDE.md law #4, no silent
degradation).
"""
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from lib.checklist_common import probe_duration, NUMBER_WORDS, LONG_NUMBER_WORD_THRESHOLD  # noqa: E402
from lib.slideshow_risk import slideshow_risk_findings  # noqa: E402

PROJECT_DIR = REPO_ROOT / "projects" / "PRJ-baskurtlar-arastirma"
REMOTION_DIR = REPO_ROOT / "remotion_baskurtlar"
SCENES_DATA = REMOTION_DIR / "src" / "scenesData.ts"
PROJECT_JSON = PROJECT_DIR / "project.json"
COMPOSITION_TSX = REMOTION_DIR / "src" / "compositions" / "StudioComposition.tsx"

LOOP_RATIO_THRESHOLD = 3.0
# check_long_compound_numbers() below stays project-local (file-based scene
# iteration + richer message text) rather than importing
# long_compound_number_findings() from lib/checklist_common.py - only the
# constants (NUMBER_WORDS, LONG_NUMBER_WORD_THRESHOLD, probe_duration) were
# confirmed byte-identical duplicates across all three checklist scripts;
# this function's body was not, so it's left alone rather than force-unified.


def check_video_loop_ratios() -> list[str]:
    findings = []
    text = SCENES_DATA.read_text()
    # Match each scene's id + visuals array + durationFrames from the
    # generated TS (same source of truth the render itself uses).
    scene_re = re.compile(
        r'id:\s*"(SC-\d+)".*?visuals:\s*(\[.*?\]),\s*startFrame:\s*\d+,\s*durationFrames:\s*(\d+)'
    )
    for m in scene_re.finditer(text):
        sid, visuals_raw, duration_frames = m.group(1), m.group(2), int(m.group(3))
        video_files = re.findall(r'"type":\s*"video",\s*"file":\s*"([^"]+)"', visuals_raw)
        n_slots = visuals_raw.count('"type"')
        if not video_files or n_slots == 0:
            continue
        slot_frames = duration_frames / n_slots
        slot_seconds = slot_frames / 30.0
        for vf in video_files:
            video_path = (REMOTION_DIR / "src" / vf).resolve()
            if not video_path.exists():
                findings.append(f"{sid}: referenced video {vf} not found on disk")
                continue
            clip_duration = probe_duration(video_path)
            if clip_duration <= 0:
                continue
            ratio = slot_seconds / clip_duration
            if ratio > LOOP_RATIO_THRESHOLD:
                findings.append(
                    f"{sid}: video clip {vf} ({clip_duration:.2f}s) loops "
                    f"{ratio:.1f}x in its {slot_seconds:.1f}s slot "
                    f"(threshold {LOOP_RATIO_THRESHOLD}x) - add more insert "
                    f"stills or a longer/second video clip"
                )
    return findings


def check_long_compound_numbers() -> list[str]:
    findings = []
    for scene_path in sorted((PROJECT_DIR / "scenes").glob("SC-*.json")):
        import json
        scene = json.loads(scene_path.read_text())
        text = scene.get("source_text", "")
        words = re.findall(r"[\wşŞğĞıİöÖüÜçÇ]+", text.lower())
        run_start = None
        run_len = 0
        for i, w in enumerate(words):
            if w in NUMBER_WORDS:
                if run_start is None:
                    run_start = i
                run_len += 1
            else:
                if run_len >= LONG_NUMBER_WORD_THRESHOLD:
                    phrase = " ".join(words[run_start:i])
                    findings.append(
                        f"{scene['scene_id']}: long compound number run ({run_len} words) "
                        f"- \"{phrase}\" - recommend a faster-whisper listen-check on "
                        f"NAR-{scene['scene_id']}.wav before render (ElevenLabs has "
                        f"garbled runs like this before, see NAR-SC-001 history)"
                    )
                run_start, run_len = None, 0
        if run_len >= LONG_NUMBER_WORD_THRESHOLD:
            phrase = " ".join(words[run_start:])
            findings.append(
                f"{scene['scene_id']}: long compound number run ({run_len} words) "
                f"- \"{phrase}\" - recommend a faster-whisper listen-check"
            )
    return findings


def main():
    all_findings = []
    if SCENES_DATA.exists():
        all_findings += check_video_loop_ratios()
    else:
        print(f"WARN: {SCENES_DATA} not found, skipping loop-ratio check", file=sys.stderr)
    all_findings += check_long_compound_numbers()
    if SCENES_DATA.exists() and PROJECT_JSON.exists():
        all_findings += slideshow_risk_findings(PROJECT_JSON, SCENES_DATA, COMPOSITION_TSX)
    else:
        print(f"WARN: {SCENES_DATA} or {PROJECT_JSON} not found, skipping slideshow-risk check", file=sys.stderr)

    if not all_findings:
        print("Pre-render checklist: clean. 0 findings.")
        sys.exit(0)

    print(f"Pre-render checklist: {len(all_findings)} finding(s) - review before full render:\n")
    for f in all_findings:
        print(f"  - {f}")
    sys.exit(1)


if __name__ == "__main__":
    main()

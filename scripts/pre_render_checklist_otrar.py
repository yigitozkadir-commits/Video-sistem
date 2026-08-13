#!/usr/bin/env python3
"""
Mandatory gate before any full Remotion render of PRJ-otrar-faciasi
(CLAUDE.md section 10 - "a future project with a different Remotion
architecture needs an equivalent script - write one before that project's
first full render, not after the first complaint").

This project's Remotion architecture differs from remotion_baskurtlar's
(the one pre_render_checklist.py was written for): a video-type visual
slot here carries an EXPLICIT durationFrames set to its own ffprobe-
measured clip length (scripts/generate_otrar_scenes_data.py), not an
even split of the scene across however many visuals it has. So the loop-
ratio check below reads that explicit value from scenesData.ts rather
than assuming duration_frames / n_slots like the Başkurtlar version - an
unmodified copy of that check would silently pass here even if something
regressed the fix, since it would understate the video's real slot length
and never flag a loop.

Checks:
1. VIDEO LOOP RATIO (Otrar-specific: explicit-duration-aware).
2. LONG COMPOUND NUMBERS IN NARRATION (same defect class documented in
   pre_render_checklist.py's header - ElevenLabs garbling long spelled-out
   Turkish numbers; ran over all 17 scenes' source_text, including the
   2026-08-09 deepening inserts).
3. Style-relative slideshow risk (scripts/lib/slideshow_risk.py, shared
   with every other project - repeated-adjacent-asset check is fully
   reusable as-is since it's file-identity based, not duration-based;
   slot_duration/motion_ceiling checks are reused too, understanding they
   average video+still slots together for a scene that has both, which
   only makes the reported average hold LOWER than the true still-only
   hold - never a false negative in the direction that matters).

This does not replace scripts/validate.py (schema conformance) or
scripts/plan_scene_count.py (Module 22 density targets) - run those too.

Usage:
    python3 scripts/pre_render_checklist_otrar.py
Exit code 0 = clean, 1 = findings need review before rendering (does not
block, just refuses to claim "all clear" - CLAUDE.md law #4).
"""
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from lib.checklist_common import probe_duration, NUMBER_WORDS, LONG_NUMBER_WORD_THRESHOLD  # noqa: E402
from lib.slideshow_risk import slideshow_risk_findings  # noqa: E402

PROJECT_DIR = REPO_ROOT / "projects" / "PRJ-otrar-faciasi"
REMOTION_DIR = REPO_ROOT / "remotion_otrar_faciasi"
SCENES_DATA = REMOTION_DIR / "src" / "scenesData.ts"
PROJECT_JSON = PROJECT_DIR / "project.json"
COMPOSITION_TSX = REMOTION_DIR / "src" / "compositions" / "StudioComposition.tsx"

LOOP_RATIO_THRESHOLD = 3.0

_SCENE_BLOCK_RE = re.compile(
    r'id:\s*"(SC-\d+)".*?visuals:\s*(\[.*?\]),\s*startFrame:\s*\d+,\s*durationFrames:\s*(\d+)'
)
_VIDEO_VISUAL_RE = re.compile(
    r'\{"type":\s*"video",\s*"file":\s*"([^"]+)"(?:,\s*"durationFrames":\s*(\d+))?\}'
)


def check_video_loop_ratios() -> list[str]:
    findings = []
    text = SCENES_DATA.read_text()
    for m in _SCENE_BLOCK_RE.finditer(text):
        sid, visuals_raw, scene_duration_frames = m.group(1), m.group(2), int(m.group(3))
        for vm in _VIDEO_VISUAL_RE.finditer(visuals_raw):
            vf, explicit_frames = vm.group(1), vm.group(2)
            video_path = (REMOTION_DIR / "src" / vf).resolve()
            if not video_path.exists():
                findings.append(f"{sid}: referenced video {vf} not found on disk")
                continue
            clip_duration = probe_duration(video_path)
            if clip_duration <= 0:
                continue
            slot_frames = int(explicit_frames) if explicit_frames else scene_duration_frames
            slot_seconds = slot_frames / 30.0
            ratio = slot_seconds / clip_duration
            if ratio > LOOP_RATIO_THRESHOLD:
                findings.append(
                    f"{sid}: video clip {vf} ({clip_duration:.2f}s) loops "
                    f"{ratio:.1f}x in its {slot_seconds:.1f}s slot "
                    f"(threshold {LOOP_RATIO_THRESHOLD}x) - the explicit-duration "
                    f"fix (scripts/generate_otrar_scenes_data.py) may not have "
                    f"been applied to this shot, check its video.json"
                )
            if not explicit_frames:
                findings.append(
                    f"{sid}: video visual {vf} has NO explicit durationFrames - "
                    f"falls back to the full scene duration ({scene_duration_frames} "
                    f"frames), which is exactly the pattern that caused the "
                    f"Başkurtlar stutter-loop bug - regenerate scenesData.ts"
                )
    return findings


def check_long_compound_numbers() -> list[str]:
    findings = []
    for scene_path in sorted(PROJECT_DIR.glob("scenes/SC-*.json")):
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
                        f"NAR-{scene['scene_id']}.wav before render"
                    )
                run_start, run_len = None, 0
        if run_len >= LONG_NUMBER_WORD_THRESHOLD:
            phrase = " ".join(words[run_start:])
            findings.append(
                f"{scene['scene_id']}: long compound number run ({run_len} words) "
                f"- \"{phrase}\" - recommend a faster-whisper listen-check"
            )
    return findings


def check_silent_scenes_no_audio_claim() -> list[str]:
    """SC-016/017 are deliberately silent (scene_type: emotional_pause,
    source_text: "") - flag it as INFO-only if scenesData.ts somehow gave
    them an audioFile (would mean the generator regressed), not a hard
    finding otherwise."""
    findings = []
    text = SCENES_DATA.read_text()
    for sid in ("SC-016", "SC-017"):
        m = re.search(rf'id:\s*"{sid}".*?audioFile:\s*(null|"[^"]*")', text)
        if m and m.group(1) != "null":
            findings.append(f"{sid}: expected to be a silent break scene but scenesData.ts gives it an audioFile ({m.group(1)}) - check scene JSON's source_text/generator")
    return findings


def main():
    all_findings = []
    if SCENES_DATA.exists():
        all_findings += check_video_loop_ratios()
        all_findings += check_silent_scenes_no_audio_claim()
    else:
        print(f"WARN: {SCENES_DATA} not found, skipping loop-ratio/silent-scene checks", file=sys.stderr)
    all_findings += check_long_compound_numbers()
    if SCENES_DATA.exists() and PROJECT_JSON.exists():
        all_findings += slideshow_risk_findings(PROJECT_JSON, SCENES_DATA, COMPOSITION_TSX)
    else:
        print(f"WARN: {SCENES_DATA} or {PROJECT_JSON} not found, skipping slideshow-risk check", file=sys.stderr)

    if not all_findings:
        print("Pre-render checklist (Otrar): clean. 0 findings.")
        sys.exit(0)

    print(f"Pre-render checklist (Otrar): {len(all_findings)} finding(s) - review before full render:\n")
    for f in all_findings:
        print(f"  - {f}")
    sys.exit(1)


if __name__ == "__main__":
    main()

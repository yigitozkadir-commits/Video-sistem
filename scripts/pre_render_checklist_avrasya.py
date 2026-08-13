#!/usr/bin/env python3
"""
Mandatory gate before any full Remotion render of PRJ-avrasya-bozkir-kusagi
(CLAUDE.md "Pre-render checklist" law - every project with a different
Remotion architecture needs its own equivalent script, written before that
project's first full render, not after the first complaint).

Checks specific to THIS project's known risk points (each one traces back to
a real defect class from PRJ-baskurtlar-arastirma's production history):

1. IMAGE COUNT MATCH. Başkurtlar's generate_baskurtlar_scenes_data.py had a
   video-scene branch that silently never called insert_shots() - the bug
   went undetected until a human watched the finished render. Here we check
   the inverse and cheaper way: does every scene actually have as many
   generated image files as its own image_count_target says it should,
   BEFORE any scenesData/render step exists to hide the gap.
2. VIDEO LOOP RATIO. Same mechanism as Başkurtlar's checklist - once
   remotion_avrasya/src/scenesData.ts exists, flag any video-type visual
   slot repeating its clip more than LOOP_RATIO_THRESHOLD times. Skipped
   with a clear note (not a false "clean") if that file doesn't exist yet.
3. BADGE-OVERLAY COMPLETENESS. The 8 [ÇOKLU] multi-reliability scenes need a
   parseable reliability_badge value for the overlay component to render
   correctly - an empty/missing badge would silently render no overlay.
4. CITATION-REF COMPLETENESS. SC-034..037 are supposed to show a source
   citation card - flag any of those four missing citation_ref.
5. LONG COMPOUND NUMBERS. Same regex-based check as Başkurtlar's script
   (ElevenLabs has garbled long spelled-out Turkish numbers before) - reused
   here since it's project-agnostic, just pointed at this project's scenes.

Usage:
    python3 scripts/pre_render_checklist_avrasya.py
Exit code 0 = clean, 1 = findings need review before rendering (does not
block, just refuses to claim "all clear" - CLAUDE.md law #4).
"""
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from lib.checklist_common import probe_duration, long_compound_number_findings  # noqa: E402
from lib.slideshow_risk import slideshow_risk_findings  # noqa: E402

PROJECT_DIR = REPO_ROOT / "projects" / "PRJ-avrasya-bozkir-kusagi"
REMOTION_DIR = REPO_ROOT / "remotion_avrasya"
SCENES_DATA = REMOTION_DIR / "src" / "scenesData.ts"
ASSETS_STILL = PROJECT_DIR / "assets" / "still"
PROJECT_JSON = PROJECT_DIR / "project.json"
COMPOSITION_TSX = REMOTION_DIR / "src" / "compositions" / "StudioComposition.tsx"

LOOP_RATIO_THRESHOLD = 3.0

CITATION_SCENES = {"SC-034", "SC-035", "SC-036", "SC-037"}


def load_scenes():
    return [json.loads(p.read_text()) for p in sorted(PROJECT_DIR.glob("scenes/SC-*.json"))]


def check_image_counts(scenes) -> list[str]:
    findings = []
    if not ASSETS_STILL.exists():
        return [f"NOTE: {ASSETS_STILL} does not exist yet - no Flow images ingested "
                f"yet, image-count check has nothing to verify against (not a failure, "
                f"just not applicable before generation)."]
    for s in scenes:
        sid = s["scene_id"]
        target = s.get("image_count_target", 0)
        actual = sum(len(list(ASSETS_STILL.glob(f"{sid}_{pat}")))
                     for pat in ("img*.jpg", "img*.png", "commons.jpg", "commons.png"))
        has_video = s.get("visual_decision") == "video"
        expected_stills = target - 1 if has_video else target
        if actual != expected_stills:
            findings.append(
                f"{sid}: image_count_target={target} ({'video+' if has_video else ''}"
                f"{expected_stills} stills expected) but {actual} still files found in "
                f"{ASSETS_STILL} - Başkurtlar's insert_shots() gap happened exactly this "
                f"way, catch it here instead of in the finished render"
            )
    return findings


def check_video_loop_ratios() -> list[str]:
    if not SCENES_DATA.exists():
        return [f"NOTE: {SCENES_DATA} does not exist yet - no Remotion composition "
                f"built yet, loop-ratio check has nothing to verify against."]
    findings = []
    text = SCENES_DATA.read_text()
    scene_re = re.compile(
        r'id:\s*"(SC-\d+)".*?visuals:\s*(\[.*?\]),\s*startFrame:\s*\d+,\s*durationFrames:\s*(\d+)'
    )

    for m in scene_re.finditer(text):
        sid, visuals_raw, duration_frames = m.group(1), m.group(2), int(m.group(3))
        video_files = re.findall(r'"type":\s*"video",\s*"file":\s*"([^"]+)"', visuals_raw)
        n_slots = visuals_raw.count('"type"')
        if not video_files or n_slots == 0:
            continue
        slot_seconds = (duration_frames / n_slots) / 30.0
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
                    f"{sid}: video clip {vf} ({clip_duration:.2f}s) loops {ratio:.1f}x "
                    f"in its {slot_seconds:.1f}s slot (threshold {LOOP_RATIO_THRESHOLD}x)"
                )
    return findings


def check_badge_completeness(scenes) -> list[str]:
    """Every scene whose badge is COKLU (multi-level) must actually list which
    levels via a ':' separator (e.g. "COKLU:KESIN+GUCLU_CIKARIM") - a bare
    "COKLU" with nothing after it would leave the overlay component with no
    levels to render."""
    findings = []
    for s in scenes:
        badge = s.get("reliability_badge")
        if badge and badge.startswith("COKLU") and ":" not in badge:
            findings.append(f"{s['scene_id']}: reliability_badge is bare 'COKLU' with no "
                             f"levels after ':' - overlay would have nothing to render")
    return findings


def check_citation_refs(scenes) -> list[str]:
    findings = []
    for s in scenes:
        if s["scene_id"] in CITATION_SCENES and not s.get("citation_ref"):
            findings.append(f"{s['scene_id']}: citation card scene but citation_ref is missing/empty")
    return findings


def main():
    scenes = load_scenes()
    all_findings = []
    all_findings += check_image_counts(scenes)
    all_findings += check_video_loop_ratios()
    all_findings += check_badge_completeness(scenes)
    all_findings += check_citation_refs(scenes)
    all_findings += long_compound_number_findings(scenes)
    if SCENES_DATA.exists() and PROJECT_JSON.exists():
        all_findings += slideshow_risk_findings(PROJECT_JSON, SCENES_DATA, COMPOSITION_TSX)
    else:
        all_findings.append(f"NOTE: {SCENES_DATA} or {PROJECT_JSON} not found, skipping slideshow-risk check")

    real_findings = [f for f in all_findings if not f.startswith("NOTE:")]
    notes = [f for f in all_findings if f.startswith("NOTE:")]

    for n in notes:
        print(n)
    if not real_findings:
        print(f"Pre-render checklist (Avrasya): clean. 0 findings ({len(notes)} not-yet-applicable note(s)).")
        sys.exit(0)

    print(f"\nPre-render checklist (Avrasya): {len(real_findings)} finding(s) - review before full render:\n")
    for f in real_findings:
        print(f"  - {f}")
    sys.exit(1)


if __name__ == "__main__":
    main()

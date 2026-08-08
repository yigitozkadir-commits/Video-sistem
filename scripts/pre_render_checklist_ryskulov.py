#!/usr/bin/env python3
"""
Mandatory gate before any full Remotion render of PRJ-ryskulov-mektubu
(CLAUDE.md "Pre-render checklist" law - every project with a different
Remotion architecture needs its own equivalent script).

Reuses PRJ-avrasya-bozkir-kusagi's checklist pattern (image counts, video
loop ratios, badge/citation completeness, long compound numbers) plus two
checks specific to this project's real risk points:

6. FORBIDDEN-CONTENT SCAN. This is a mass-death, genocide-adjacent subject
   (Aşarşılık, 1930-1933). style/archival_restrained_documentary.json's
   forbidden list (no corpses/starving bodies/execution/reenactment/human
   figures) and required negative-prompt suffix must actually appear in
   every prompts_used/*/image.json and video.json's negative field - a
   missing negative clause is exactly how Avrasya's specimen-label defect
   slipped through undetected until visual inspection.
7. NUMERIC FIDELITY. state/numeric_fidelity_check.json (written by
   scripts/numeric_fidelity_check_ryskulov.py) must show status "clean" -
   an unresolved finding there means a spoken figure doesn't match the
   source docx, and this project has no Remotion-native chart to catch the
   error visually (the number only ever exists as narration audio).

Usage:
    python3 scripts/pre_render_checklist_ryskulov.py
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

PROJECT_DIR = REPO_ROOT / "projects" / "PRJ-ryskulov-mektubu"
REMOTION_DIR = REPO_ROOT / "remotion_ryskulov"
SCENES_DATA = REMOTION_DIR / "src" / "scenesData.ts"
ASSETS_STILL = PROJECT_DIR / "assets" / "still"
PROMPTS_DIR = PROJECT_DIR / "prompts_used"
STYLE_PATH = REPO_ROOT / "style" / "archival_restrained_documentary.json"
NUMERIC_FIDELITY_PATH = PROJECT_DIR / "state" / "numeric_fidelity_check.json"

LOOP_RATIO_THRESHOLD = 3.0

CITATION_SCENES = {"SC-018", "SC-019", "SC-020", "SC-021", "SC-022", "SC-023",
                    "SC-025", "SC-027", "SC-034", "SC-035", "SC-037", "SC-038",
                    "SC-039", "SC-041"}

# Terms that must appear in EVERY generated-image prompt's negative field -
# the code-level enforcement of style/archival_restrained_documentary.json's
# forbidden list, for this specific mass-death subject.
REQUIRED_NEGATIVE_TERMS_UNIVERSAL = ["corpses", "starving", "execution", "weapons", "reenactment"]
# Extra terms required ONLY on statistic-heavy scenes (scaffold script's
# stats_scene=True) - these are the ones asking Flow not to bake in readable
# figures, per the Avrasya specimen-label lesson (scripts/scaffold_ryskulov_
# project.py's NEGATIVE_STATS_EXTRA). Scene IDs match SCENES entries with
# stats_scene=True that actually generate their own image (not "reuse").
STATS_SCENE_IDS = {"SC-018", "SC-020", "SC-022", "SC-044"}
REQUIRED_NEGATIVE_TERMS_STATS = ["readable chart labels", "readable numbers"]


def load_scenes():
    return [json.loads(p.read_text()) for p in sorted(PROJECT_DIR.glob("scenes/SC-*.json"))]


def check_image_counts(scenes) -> list[str]:
    findings = []
    has_any_still = ASSETS_STILL.exists() and any(ASSETS_STILL.iterdir())
    if not has_any_still:
        return [f"NOTE: {ASSETS_STILL} has no files yet - no Flow images ingested "
                f"yet, image-count check has nothing to verify against."]
    for s in scenes:
        sid = s["scene_id"]
        if s["visual_decision"] == "reuse":
            continue
        target = s.get("image_count_target", 0)
        has_video = s.get("visual_decision") == "video"
        actual = sum(len(list(ASSETS_STILL.glob(f"{sid}_{pat}"))) for pat in ("img*.jpg", "img*.png"))
        expected_stills = 0 if has_video else target
        if has_video:
            continue  # video-decision scenes: the still is a fallback only, not a hard count requirement
        if actual != expected_stills:
            findings.append(
                f"{sid}: image_count_target={target} but {actual} still files found in {ASSETS_STILL}"
            )
    return findings


def check_video_loop_ratios() -> list[str]:
    if not SCENES_DATA.exists():
        return [f"NOTE: {SCENES_DATA} does not exist yet - no Remotion composition built yet."]
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
    findings = []
    for s in scenes:
        badge = s.get("reliability_badge")
        if badge and badge.startswith("COKLU") and ":" not in badge:
            findings.append(f"{s['scene_id']}: reliability_badge is bare 'COKLU' with no levels after ':'")
    return findings


def check_citation_refs(scenes) -> list[str]:
    findings = []
    for s in scenes:
        if s["scene_id"] in CITATION_SCENES and not s.get("citation_ref"):
            findings.append(f"{s['scene_id']}: citation card scene but citation_ref is missing/empty")
    return findings


def check_forbidden_content_negatives() -> list[str]:
    if not PROMPTS_DIR.exists() or not any(PROMPTS_DIR.iterdir()):
        return ["NOTE: prompts_used/ is empty - nothing to scan yet."]
    if not STYLE_PATH.exists():
        return [f"ERROR: {STYLE_PATH} not found - cannot verify required negative terms"]
    findings = []
    for prompt_file in sorted(PROMPTS_DIR.glob("*/image.json")) + sorted(PROMPTS_DIR.glob("*/video.json")):
        req = json.loads(prompt_file.read_text())
        negative = req.get("negative", "").lower()
        missing = [t for t in REQUIRED_NEGATIVE_TERMS_UNIVERSAL if t not in negative]
        # shot_id "SH-018-01" -> scene_id "SC-018"
        scene_id = "SC-" + prompt_file.parent.name.split("-")[1]
        if scene_id in STATS_SCENE_IDS:
            missing += [t for t in REQUIRED_NEGATIVE_TERMS_STATS if t not in negative]
        if missing:
            findings.append(
                f"{prompt_file.parent.name}/{prompt_file.name}: missing required negative term(s): {missing}"
            )
    return findings


def check_numeric_fidelity() -> list[str]:
    if not NUMERIC_FIDELITY_PATH.exists():
        return [f"NOTE: {NUMERIC_FIDELITY_PATH} not found - run "
                f"scripts/numeric_fidelity_check_ryskulov.py before rendering."]
    data = json.loads(NUMERIC_FIDELITY_PATH.read_text())
    if data.get("status") != "clean":
        return [f"numeric_fidelity_check.json status is '{data.get('status')}' - "
                f"{len(data.get('findings', []))} unresolved numeric finding(s), see the file directly"]
    return []


def main():
    scenes = load_scenes()
    all_findings = []
    all_findings += check_image_counts(scenes)
    all_findings += check_video_loop_ratios()
    all_findings += check_badge_completeness(scenes)
    all_findings += check_citation_refs(scenes)
    all_findings += long_compound_number_findings(scenes)
    all_findings += check_forbidden_content_negatives()
    all_findings += check_numeric_fidelity()

    real_findings = [f for f in all_findings if not f.startswith("NOTE:")]
    notes = [f for f in all_findings if f.startswith("NOTE:")]

    for n in notes:
        print(n)
    if not real_findings:
        print(f"Pre-render checklist (Ryskulov): clean. 0 findings ({len(notes)} not-yet-applicable note(s)).")
        sys.exit(0)

    print(f"\nPre-render checklist (Ryskulov): {len(real_findings)} finding(s) - review before full render:\n")
    for f in real_findings:
        print(f"  - {f}")
    sys.exit(1)


if __name__ == "__main__":
    main()

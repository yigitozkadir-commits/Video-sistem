"""
Style-relative slideshow-risk scoring (OpenMontage-inspired, see
HANDOFF_OPENMONTAGE_PROPOSAL.md item 1.3 for the full evaluation).

A blind "this scene is static" check is wrong for this studio: several
projects (e.g. PRJ-ninniler-atlasi) are *deliberately* slideshows -
motion_ceiling: 1-2, still_video_ratio > 0.5 by template design. The risk
signal that actually matters is a scene being MORE static/repetitive than
its OWN style profile and template call for, not staticness in the
absolute. All three checks below are relative to real per-project config
(templates/*.json's director.pace, style/*.json's motion_ceiling) - never
a fixed constant - matching this module's naming.

Advisory only, same contract as lib/checklist_common.py: callers print
these as findings to review, never a block. A project with 0 findings has
been checked, not "proven perfect" - real T1/T2/T3 QA per Module_12 still
applies.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent

# Same tolerance philosophy as pre_render_checklist.py's LOOP_RATIO_THRESHOLD:
# a slot moderately over the template's own declared upper pacing bound is
# normal (last slot in a scene absorbs a rounding remainder); one that blows
# past it by SLOT_OVERAGE_FACTOR is worth a look.
SLOT_OVERAGE_FACTOR = 1.5

# StudioComposition.tsx's own comment ("restrained - matches motion_ceiling:
# 1 in most style profiles") documents this pairing as the calibrated
# baseline - not a number invented for this check.
CALIBRATED_CEILING = 1
CALIBRATED_KEN_BURNS_SCALE = 1.03
SCALE_EPSILON = 0.005  # float-compare slack

# Scene-object field order is NOT consistent across data files - the
# SceneData TS interface lists visuals before startFrame/durationFrames,
# and scenesData.ts's own literals follow that order, but lullabies.ts (a
# separately hand-evolved file - see git history) puts durationFrames
# before visuals. Rather than assume an order, find each scene id, then
# search the text window up to the NEXT scene id independently for
# visuals/durationFrames - order-agnostic by construction. Scene ids in
# this codebase are always uppercase ("SC-001", "KAZAK") - the id: field
# on the enclosing Lullaby object ("ninni-kazak") is lowercase and never
# matches, so windows never accidentally span a lullaby boundary.
_SCENE_ID_RE = re.compile(r'id:\s*"([A-Z][A-Z0-9_-]*)"')
_VISUALS_ARRAY_RE = re.compile(r"visuals:\s*(\[.*?\])\s*,", re.DOTALL)
_DURATION_FRAMES_RE = re.compile(r"durationFrames:\s*(\d+)")
# Unquoted TS object keys (`{ type: "still", file: "..." }`), not JSON -
# confirmed against real scenesData.ts/lullabies.ts data (a quoted-key
# variant of this regex silently matched 0 files against real files).
_VISUAL_FILE_RE = re.compile(r'file:\s*"([^"]+)"')


def _sha256_file(path: Path, _cache: dict = {}) -> str | None:
    key = str(path)
    if key in _cache:
        return _cache[key]
    if not path.exists():
        _cache[key] = None
        return None
    h = hashlib.sha256()
    h.update(path.read_bytes())
    digest = h.hexdigest()
    _cache[key] = digest
    return digest


def resolve_template_pace(template_ref: str, _seen: frozenset = frozenset()) -> dict | None:
    """Reads templates/<template_ref>.json's director.pace, following a
    single-level 'extends' chain if the template doesn't define its own
    pace (matches the one level of nesting actually used in templates/ -
    e.g. TPL-archival-documentary -> TPL-documentary)."""
    if template_ref in _seen:
        return None  # cycle guard, never expected in real data
    path = REPO_ROOT / "templates" / f"{template_ref}.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    pace = data.get("director", {}).get("pace")
    if pace:
        return pace
    parent = data.get("extends")
    if parent:
        return resolve_template_pace(parent, _seen | {template_ref})
    return None


def parse_scene_blocks(ts_text: str) -> list[dict]:
    """Returns [{"scene_id", "duration_frames", "files": [str, ...]}] in
    file order, for either scenesData.ts's flat SCENES array or
    lullabies.ts's nested LULLABIES[].scenes[] shape - both use the same
    per-scene id/visuals/durationFrames fields, just nested differently
    (and in a different field order - see _SCENE_ID_RE's comment)."""
    id_matches = list(_SCENE_ID_RE.finditer(ts_text))
    blocks = []
    for idx, m in enumerate(id_matches):
        window_end = id_matches[idx + 1].start() if idx + 1 < len(id_matches) else len(ts_text)
        window = ts_text[m.end():window_end]
        visuals_m = _VISUALS_ARRAY_RE.search(window)
        duration_m = _DURATION_FRAMES_RE.search(window)
        if not visuals_m or not duration_m:
            continue
        files = _VISUAL_FILE_RE.findall(visuals_m.group(1))
        if files:
            blocks.append({"scene_id": m.group(1), "duration_frames": int(duration_m.group(1)), "files": files})
    return blocks


def slot_duration_findings(scenes: list[dict], fps: int, pace: dict | None) -> list[str]:
    if not pace or not pace.get("range"):
        return []
    ceiling_s = pace["range"][1] * SLOT_OVERAGE_FACTOR
    findings = []
    for s in scenes:
        n_slots = len(s["files"])
        if n_slots == 0:
            continue
        slot_s = (s["duration_frames"] / fps) / n_slots
        if slot_s > ceiling_s:
            findings.append(
                f"{s['scene_id']}: visual slot holds {slot_s:.1f}s, over "
                f"{SLOT_OVERAGE_FACTOR}x the template's declared pace range "
                f"upper bound ({pace['range'][1]}s) - static-image risk, "
                f"consider splitting into more slots"
            )
    return findings


def repeated_adjacent_asset_findings(scenes: list[dict], ts_path: Path) -> list[str]:
    """Flags the same image/video file appearing in back-to-back slots -
    across a scene's own slots AND across a scene boundary (both real
    shapes exist in this repo: scenesData.ts has many scenes/few slots
    each, lullabies.ts has one scene/many slots) - a genuinely repeated
    frame is a defect regardless of style, so this check is NOT
    style-relative like the other two."""
    flat: list[tuple[str, str]] = []  # (scene_id, file)
    for s in scenes:
        for f in s["files"]:
            flat.append((s["scene_id"], f))

    base_dir = ts_path.parent
    findings = []
    for i in range(1, len(flat)):
        prev_scene, prev_file = flat[i - 1]
        cur_scene, cur_file = flat[i]
        if prev_file == cur_file:
            findings.append(
                f"{cur_scene}: same file used in back-to-back visual slots "
                f"({cur_file}) - identical adjacent frame"
            )
            continue
        prev_hash = _sha256_file((base_dir / prev_file).resolve())
        cur_hash = _sha256_file((base_dir / cur_file).resolve())
        if prev_hash is not None and prev_hash == cur_hash:
            findings.append(
                f"{cur_scene}: back-to-back visual slots are byte-identical "
                f"despite different filenames ({prev_file} == {cur_file})"
            )
    return findings


def motion_ceiling_findings(composition_tsx_text: str, motion_ceiling: int | None) -> list[str]:
    if motion_ceiling is None or motion_ceiling <= CALIBRATED_CEILING:
        return []
    m = re.search(r"KEN_BURNS_SCALE\s*=\s*([\d.]+)", composition_tsx_text)
    if not m:
        return []
    scale = float(m.group(1))
    if scale <= CALIBRATED_KEN_BURNS_SCALE + SCALE_EPSILON:
        return [
            f"style profile declares motion_ceiling={motion_ceiling} (more motion "
            f"than the ceiling-{CALIBRATED_CEILING} baseline) but the render's "
            f"KEN_BURNS_SCALE constant is still {scale} (the restrained value "
            f"calibrated for motion_ceiling={CALIBRATED_CEILING}) - stills will "
            f"look flatter/more static than this style profile intends"
        ]
    return []


def slideshow_risk_findings(project_json_path: Path, scenes_ts_path: Path, composition_tsx_path: Path) -> list[str]:
    """Top-level entrypoint a project's pre_render_checklist_*.py wires in
    the same way it already calls check_video_loop_ratios(). Any missing
    input file degrades to 'skip that sub-check', never a crash - the
    checklist scripts already guard the same way around missing
    SCENES_DATA (CLAUDE.md law #4: a skip must still be visible, so callers
    should print a WARN like pre_render_checklist.py's SCENES_DATA guard,
    this function only returns what it could check)."""
    findings: list[str] = []
    if not project_json_path.exists() or not scenes_ts_path.exists():
        return findings

    project = json.loads(project_json_path.read_text())
    fps = project.get("output", {}).get("fps", 30)
    template_ref = project.get("template_ref")
    style_ref = project.get("style_profile_ref")

    pace = resolve_template_pace(template_ref) if template_ref else None
    motion_ceiling = None
    if style_ref:
        style_path = REPO_ROOT / style_ref
        if style_path.exists():
            motion_ceiling = json.loads(style_path.read_text()).get("motion_ceiling")

    scenes = parse_scene_blocks(scenes_ts_path.read_text())
    findings += slot_duration_findings(scenes, fps, pace)
    findings += repeated_adjacent_asset_findings(scenes, scenes_ts_path)

    if composition_tsx_path.exists():
        findings += motion_ceiling_findings(composition_tsx_path.read_text(), motion_ceiling)

    return findings

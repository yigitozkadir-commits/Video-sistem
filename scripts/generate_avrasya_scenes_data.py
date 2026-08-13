#!/usr/bin/env python3
"""
Generates remotion_avrasya/src/scenesData.ts from MEASURED audio durations.

Narration is the clock (CLAUDE.md law #3): each scene's timeline duration is
now derived from its own NAR-SC-*.wav's real length via ffprobe, never the
planned duration_estimate_s - same switch generate_baskurtlar_scenes_data.py
made once real ElevenLabs narration existed. Seconds -> frames converted once
at this timeline boundary (round(seconds * fps)).

Visual selection logic (image_count_target ordering, video-scene handling,
Commons-photo slot) is unchanged from the preview-stage version of this
script - only the duration source changed.

Re-run whenever assets/audio/NAR-SC-*.wav or the scene visual assignment
changes.

Usage:
    python3 scripts/generate_avrasya_scenes_data.py
"""
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from lib.checklist_common import probe_duration  # noqa: E402

PROJECT_DIR = REPO_ROOT / "projects" / "PRJ-avrasya-bozkir-kusagi"
REMOTION_DIR = REPO_ROOT / "remotion_avrasya"
FPS = 30


def visuals_for(scene: dict, public_dir: Path) -> list[dict]:
    sid = scene["scene_id"]
    target = scene.get("image_count_target", 0)
    has_video = scene.get("visual_decision") == "video"
    visuals = []

    if has_video:
        vpath = public_dir / "video" / f"{sid}_video.mp4"
        if vpath.exists():
            visuals.append({"type": "video", "file": f"../public/video/{sid}_video.mp4"})
        n_stills = target - 1
    else:
        n_stills = target

    for n in range(1, n_stills + 1):
        for ext in (".jpg", ".png"):
            spath = public_dir / "still" / f"{sid}_img{n}{ext}"
            if spath.exists():
                visuals.append({"type": "still", "file": f"../public/still/{sid}_img{n}{ext}"})
                break

    # SC-017 also has a real Commons photo covering one of its slots
    commons_path = public_dir / "still" / f"{sid}_commons.jpg"
    if commons_path.exists():
        visuals.append({"type": "still", "file": f"../public/still/{sid}_commons.jpg"})

    return visuals


def main():
    public_dir = REMOTION_DIR / "public"
    scenes_out = []
    cursor_frame = 0
    missing_report = []

    for scene_path in sorted(PROJECT_DIR.glob("scenes/SC-*.json")):
        scene = json.loads(scene_path.read_text())
        sid = scene["scene_id"]
        visuals = visuals_for(scene, public_dir)
        target = scene.get("image_count_target", 0)
        if len(visuals) < target:
            missing_report.append(f"{sid}: {len(visuals)}/{target} visuals present")

        audio_path = PROJECT_DIR / "assets" / "audio" / f"NAR-{sid}.wav"
        audio_duration_s = probe_duration(audio_path)
        duration_frames = round(audio_duration_s * FPS)

        scenes_out.append({
            "id": sid,
            "title": scene["title"],
            "audioFile": f"../public/audio/NAR-{sid}.wav",
            "visuals": visuals,
            "startFrame": cursor_frame,
            "durationFrames": duration_frames,
            "audioDurationS": round(audio_duration_s, 3),
        })
        cursor_frame += duration_frames

    total_frames = cursor_frame

    lines = [
        "// AUTO-GENERATED from measured audio durations (ffprobe). Do not hand-edit.",
        "// Regenerate with scripts/generate_avrasya_scenes_data.py whenever",
        "// assets/audio/NAR-SC-*.wav or the scene visual assignment changes.",
        "export interface SceneVisual {",
        '  type: "video" | "still";',
        "  file: string;",
        "}",
        "",
        "export interface SceneData {",
        "  id: string;",
        "  title: string;",
        "  audioFile: string;",
        "  visuals: SceneVisual[];",
        "  startFrame: number;",
        "  durationFrames: number;",
        "}",
        "",
        f"export const TOTAL_FRAMES = {total_frames};",
        f"export const FPS = {FPS};",
        "",
        "export const SCENES: SceneData[] = [",
    ]
    for s in scenes_out:
        visuals_json = json.dumps(s["visuals"], ensure_ascii=False)
        title_json = json.dumps(s["title"], ensure_ascii=False)
        lines.append(
            f'  {{ id: "{s["id"]}", title: {title_json}, audioFile: "{s["audioFile"]}", '
            f'visuals: {visuals_json}, startFrame: {s["startFrame"]}, '
            f'durationFrames: {s["durationFrames"]} }}, // audio {s["audioDurationS"]}s'
        )
    lines.append("];")

    out_path = REMOTION_DIR / "src" / "scenesData.ts"
    out_path.write_text("\n".join(lines) + "\n")

    print(f"Wrote {out_path.relative_to(REPO_ROOT)}: {len(scenes_out)} scenes, "
          f"{total_frames} total frames ({total_frames/FPS/60:.2f} min, measured audio)")
    if missing_report:
        print(f"\n{len(missing_report)} scene(s) with incomplete visuals:")
        for m in missing_report:
            print(f"  {m}")


if __name__ == "__main__":
    main()

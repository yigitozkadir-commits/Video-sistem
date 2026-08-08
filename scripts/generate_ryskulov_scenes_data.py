#!/usr/bin/env python3
"""
Generates remotion_ryskulov/src/scenesData.ts from MEASURED audio durations.

Narration is the clock (CLAUDE.md law #3): switched from the scaffold-stage
"planned duration_estimate_s" model to ffprobe-measured NAR-SC-*.wav
durations, now that real ElevenLabs narration exists for 45/46 scenes
(scripts/generate_ryskulov_narration.py). SC-001 (title card) has no
narration by design - falls back to its planned duration_estimate_s.

Visual selection logic (image_count_target ordering, video-decision
handling, reuse-scene borrowing) is unchanged from the preview-stage
version of this script.

Re-run whenever assets/audio/NAR-SC-*.wav or the scene visual assignment
changes.

Usage:
    python3 scripts/generate_ryskulov_scenes_data.py
"""
import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
PROJECT_DIR = REPO_ROOT / "projects" / "PRJ-ryskulov-mektubu"
REMOTION_DIR = REPO_ROOT / "remotion_ryskulov"
FPS = 30


def probe_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True,
    ).stdout.strip()
    return float(out) if out else 0.0


def still_paths(public_dir: Path, sid: str) -> list[str]:
    """All {sid}_imgN.{jpg,png} files present, sorted by N."""
    found: dict[int, str] = {}
    for ext in (".jpg", ".png"):
        for p in public_dir.glob(f"still/{sid}_img*{ext}"):
            try:
                n = int(p.stem.split("_img")[1])
            except (IndexError, ValueError):
                continue
            found.setdefault(n, f"../public/still/{p.name}")
    return [found[n] for n in sorted(found)]


def visuals_for(scene: dict, public_dir: Path) -> list[dict]:
    sid = scene["scene_id"]
    visual_decision = scene["visual_decision"]

    if visual_decision == "reuse":
        ref_sids = scene.get("visual_reuse_of") or []
        visuals = []
        for ref in ref_sids:
            for sp in still_paths(public_dir, ref):
                visuals.append({"type": "still", "file": sp})
        return visuals

    if visual_decision == "video":
        vpath = public_dir / "video" / f"{sid}_video.mp4"
        if vpath.exists():
            return [{"type": "video", "file": f"../public/video/{sid}_video.mp4"}]

    return [{"type": "still", "file": sp} for sp in still_paths(public_dir, sid)]


def main():
    public_dir = REMOTION_DIR / "public"
    audio_dir = PROJECT_DIR / "assets" / "audio"
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

        audio_path = audio_dir / f"NAR-{sid}.wav"
        if audio_path.exists():
            duration_s = probe_duration(audio_path)
            audio_file = f"../public/audio/NAR-{sid}.wav"
        else:
            duration_s = scene["duration_estimate_s"]
            audio_file = None
        duration_frames = round(duration_s * FPS)

        scenes_out.append({
            "id": sid,
            "title": scene["title"],
            "audioFile": audio_file,
            "visuals": visuals,
            "startFrame": cursor_frame,
            "durationFrames": duration_frames,
            "audioDurationS": round(duration_s, 3),
        })
        cursor_frame += duration_frames

    total_frames = cursor_frame

    lines = [
        "// AUTO-GENERATED from measured audio durations (ffprobe) where available,",
        "// planned duration_estimate_s otherwise (SC-001 title card has no narration).",
        "// Regenerate with scripts/generate_ryskulov_scenes_data.py whenever",
        "// assets/audio/NAR-SC-*.wav or the scene visual assignment changes.",
        "export interface SceneVisual {",
        '  type: "video" | "still";',
        "  file: string;",
        "}",
        "",
        "export interface SceneData {",
        "  id: string;",
        "  title: string;",
        "  audioFile: string | null;",
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
        audio_json = json.dumps(s["audioFile"], ensure_ascii=False)
        lines.append(
            f'  {{ id: "{s["id"]}", title: {title_json}, audioFile: {audio_json}, '
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

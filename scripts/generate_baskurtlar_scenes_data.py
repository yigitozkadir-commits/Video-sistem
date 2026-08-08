#!/usr/bin/env python3
"""
Generates remotion_baskurtlar/src/scenesData.ts from measured audio durations.

Narration is the clock (CLAUDE.md law #3): each scene's timeline duration is
derived from its own NAR-SC-*.wav's real length via ffprobe, never assumed.
Seconds are converted to frames once, at this timeline boundary
(round(seconds * fps)).

Reuse scenes (scenes/SC-*.json visual_decision == "reuse") get a visuals[]
slideshow built from their visual_reuse_of target scenes' STILL image only
(never the target's video clip) - the four AI-video hero moments
(SC-001/005/007/011) stay unique to their own scene, per production
decision; a montage/reuse scene splits its duration evenly across however
many stills it lists, cross-fading between them.

Re-run whenever assets/audio/NAR-SC-*.wav or the scene visual assignment
changes.
"""
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from lib.checklist_common import probe_duration  # noqa: E402

FPS = 30
PROJECT_DIR = REPO_ROOT / "projects" / "PRJ-baskurtlar-arastirma"
OUT_PATH = REPO_ROOT / "remotion_baskurtlar" / "src" / "scenesData.ts"

# Scenes whose own primary visual is the AI-generated motion clip rather
# than a still. All four also have a still (dual-prompt rule, CLAUDE.md
# §5b) which is what gets used if another scene reuses them.
VIDEO_SCENE_IDS = {"SC-001", "SC-005", "SC-007", "SC-011"}


def insert_shots(sid: str) -> list[str]:
    """SC-{sid}_insert{N}.jpg cutaways added after the primary still to break
    up long single-image holds (user feedback: static images bore viewers).
    Sourced from remotion_baskurtlar/public/still/, sorted by insert index."""
    still_dir = REPO_ROOT / "remotion_baskurtlar" / "public" / "still"
    inserts = sorted(
        still_dir.glob(f"{sid}_insert*.jpg"),
        key=lambda p: int(p.stem.split("insert")[1]),
    )
    return [f"../public/still/{p.name}" for p in inserts]


def visuals_for(scene: dict) -> list[dict]:
    sid = scene["scene_id"]
    if scene["visual_decision"] == "reuse":
        visuals = [
            {"type": "still", "file": f"../public/still/{ref}.jpg"}
            for ref in scene["visual_reuse_of"]
        ]
        visuals += [{"type": "still", "file": f} for f in insert_shots(sid)]
        return visuals
    if sid in VIDEO_SCENE_IDS:
        visuals = [{"type": "video", "file": f"../public/video/SH-{sid}.mp4"}]
        visuals += [{"type": "still", "file": f} for f in insert_shots(sid)]
        return visuals
    visuals = [{"type": "still", "file": f"../public/still/{sid}.jpg"}]
    visuals += [{"type": "still", "file": f} for f in insert_shots(sid)]
    return visuals


def main():
    scene_paths = sorted((PROJECT_DIR / "scenes").glob("SC-*.json"))
    scenes = []
    cumulative_frame = 0

    for p in scene_paths:
        scene = json.loads(p.read_text())
        sid = scene["scene_id"]
        audio_path = PROJECT_DIR / "assets" / "audio" / f"NAR-{sid}.wav"
        audio_duration_s = probe_duration(audio_path)
        duration_frames = round(audio_duration_s * FPS)
        scenes.append({
            "id": sid,
            "title": scene["title"],
            "audioFile": f"../public/audio/NAR-{sid}.wav",
            "visuals": visuals_for(scene),
            "startFrame": cumulative_frame,
            "durationFrames": duration_frames,
            "audioDurationS": round(audio_duration_s, 3),
        })
        cumulative_frame += duration_frames

    total_frames = cumulative_frame
    print(f"Total frames: {total_frames}  Total seconds: {total_frames / FPS:.2f}  "
          f"({total_frames / FPS / 60:.2f} min)")

    lines = [
        "// AUTO-GENERATED from measured audio durations (ffprobe). Do not hand-edit.",
        "// Regenerate with scripts/generate_baskurtlar_scenes_data.py whenever",
        "// assets/audio/NAR-SC-*.wav or the scene visual assignment changes.",
        'export interface SceneVisual {',
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
    for s in scenes:
        visuals_json = json.dumps(s["visuals"], ensure_ascii=False)
        title_json = json.dumps(s["title"], ensure_ascii=False)
        lines.append(
            f'  {{ id: "{s["id"]}", title: {title_json}, audioFile: "{s["audioFile"]}", '
            f'visuals: {visuals_json}, startFrame: {s["startFrame"]}, '
            f'durationFrames: {s["durationFrames"]} }}, // audio {s["audioDurationS"]}s'
        )
    lines.append("];")

    OUT_PATH.write_text("\n".join(lines) + "\n")
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Generates remotion_studio/src/scenesData.ts from measured audio durations.

Narration is the clock (CLAUDE.md law #3): each scene's timeline duration
is derived from its own narration file's real length via ffprobe, never
assumed. Seconds are converted to frames once, at this timeline boundary
(round(seconds * fps)), per CLAUDE.md's hard rules.

Re-run this whenever assets/audio/NAR-SC-*.wav changes.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lib.checklist_common import probe_duration  # noqa: E402

FPS = 30
VIDEO_SCENES = {1, 8, 15, 25, 35, 45}
REPO_ROOT = "/home/user/Sesli-kitap-st-dyosu"


def main():
    scenes = []
    cumulative_frame = 0

    for i in range(1, 49):
        scene_id = f"SC-{i:03d}"
        audio_path = f"{REPO_ROOT}/projects/PRJ-daglar-uyuyan-devleri/assets/audio/NAR-{scene_id}.wav"
        audio_duration_s = probe_duration(audio_path)
        duration_frames = round(audio_duration_s * FPS)
        is_video = i in VIDEO_SCENES
        visual_file = (
            f"../public/video/SH-{scene_id}.mp4"
            if is_video
            else f"../public/still/{scene_id}.png"
        )
        scenes.append({
            "id": scene_id,
            "type": "video" if is_video else "still",
            "audioFile": f"../public/audio/NAR-{scene_id}.wav",
            "visualFile": visual_file,
            "startFrame": cumulative_frame,
            "durationFrames": duration_frames,
            "audioDurationS": round(audio_duration_s, 3),
        })
        cumulative_frame += duration_frames

    total_frames = cumulative_frame
    print(f"Total frames: {total_frames}  Total seconds: {total_frames / FPS:.2f}  ({total_frames / FPS / 60:.2f} min)")

    lines = [
        "// AUTO-GENERATED from measured audio durations (ffprobe). Do not hand-edit.",
        "// Regenerate with scripts/generate_scenes_data.py whenever audio assets change.",
        "export interface SceneData {",
        "  id: string;",
        '  type: "video" | "still";',
        "  audioFile: string;",
        "  visualFile: string;",
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
        lines.append(
            f'  {{ id: "{s["id"]}", type: "{s["type"]}", audioFile: "{s["audioFile"]}", '
            f'visualFile: "{s["visualFile"]}", startFrame: {s["startFrame"]}, durationFrames: {s["durationFrames"]} }}, '
            f'// audio {s["audioDurationS"]}s'
        )
    lines.append("];")

    out_path = f"{REPO_ROOT}/remotion_studio/src/scenesData.ts"
    with open(out_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()

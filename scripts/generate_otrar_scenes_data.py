#!/usr/bin/env python3
"""
Generates remotion_otrar_faciasi/src/scenesData.ts from measured audio
durations (narration is the clock - CLAUDE.md law #3).

Otrar's scene model differs from every prior project this studio has
rendered: a scene can mix ONE ai-video shot with SEVERAL still shots in
the same scene (SC-003/006/008), and two scenes are deliberately silent
(SC-016/017, "sessiz mola" - visual only, no audioFile). The plain
even-split-across-visuals model in remotion_template's StudioComposition
is what produced the historical Başkurtlar stutter-loop bug (a 6s clip
assigned an even 1/N slot of the scene, looping 5.6-13.7x, only caught by
a human watching the finished render - CLAUDE.md section 10). This script
instead:

  - gives each video-type shot an explicit durationFrames = its own
    ffprobe-measured clip length (video.json's duration_actual_s),
  - lets the remaining still shots split whatever frames are left evenly,
  - fixes the two silent scenes at exactly 10s with a single still and no
    audioFile.

The scene PLAYBACK order is projects/<id>/state/scene_plan.json's
final_sequence_order (2026-08-09 deepening insert), not scene_id sort
order - the continuity_from chain (see scenes/SC-*.json) agrees with it,
verified separately (see scene_plan.json's final_render_timeline note).

Re-run whenever assets/audio/NAR-SC-*.wav or any scene's shot list changes.
"""
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from lib.checklist_common import probe_duration  # noqa: E402

FPS = 30
PROJECT_DIR = REPO_ROOT / "projects" / "PRJ-otrar-faciasi"
OUT_PATH = REPO_ROOT / "remotion_otrar_faciasi" / "src" / "scenesData.ts"
SILENT_SCENE_DURATION_S = 10.0


def visuals_for(scene: dict) -> list[dict]:
    visuals = []
    for shot_id in scene["shots"]:
        video_json = PROJECT_DIR / "prompts_used" / shot_id / "video.json"
        image_json = PROJECT_DIR / "prompts_used" / shot_id / "image.json"
        if video_json.exists():
            v = json.loads(video_json.read_text())
            dur_s = v["duration_actual_s"]
            rel = "../public/video/" + Path(v["local_path"]).name
            visuals.append({"type": "video", "file": rel, "durationFrames": round(dur_s * FPS)})
        else:
            img = json.loads(image_json.read_text())
            rel = "../public/still/" + Path(img["local_path"]).name
            visuals.append({"type": "still", "file": rel})
    return visuals


def main():
    plan = json.loads((PROJECT_DIR / "state" / "scene_plan.json").read_text())
    order = plan["deepening_insert_2026_08_09"]["final_sequence_order"]

    scenes = []
    cumulative_frame = 0
    for sid in order:
        scene = json.loads((PROJECT_DIR / "scenes" / f"{sid}.json").read_text())
        audio_path = PROJECT_DIR / "assets" / "audio" / f"NAR-{sid}.wav"
        has_audio = audio_path.exists()
        if has_audio:
            audio_duration_s = probe_duration(audio_path)
            duration_frames = round(audio_duration_s * FPS)
            audio_file = f"../public/audio/NAR-{sid}.wav"
        else:
            audio_duration_s = SILENT_SCENE_DURATION_S
            duration_frames = round(SILENT_SCENE_DURATION_S * FPS)
            audio_file = None

        scenes.append({
            "id": sid,
            "title": scene["title"],
            "audioFile": audio_file,
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
        "// Regenerate with scripts/generate_otrar_scenes_data.py whenever",
        "// assets/audio/NAR-SC-*.wav or a scene's shot list changes.",
        'import type { Caption } from "@remotion/captions";',
        "",
        'export interface SceneVisual {',
        '  type: "video" | "still";',
        "  file: string;",
        "  // Explicit slot length in frames - set for video shots (their own",
        "  // ffprobe-measured clip duration, see file header). Omitted for",
        "  // still shots, which split whatever frames remain evenly.",
        "  durationFrames?: number;",
        '}',
        "",
        "export interface SceneData {",
        "  id: string;",
        "  title: string;",
        "  audioFile: string | null;",
        "  visuals: SceneVisual[];",
        "  startFrame: number;",
        "  durationFrames: number;",
        "  captions?: Caption[];",
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
        audio_json = "null" if s["audioFile"] is None else json.dumps(s["audioFile"], ensure_ascii=False)
        lines.append(
            f'  {{ id: "{s["id"]}", title: {title_json}, audioFile: {audio_json}, '
            f'visuals: {visuals_json}, startFrame: {s["startFrame"]}, '
            f'durationFrames: {s["durationFrames"]} }}, // audio {s["audioDurationS"]}s'
        )
    lines.append("];")

    OUT_PATH.write_text("\n".join(lines) + "\n")
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()

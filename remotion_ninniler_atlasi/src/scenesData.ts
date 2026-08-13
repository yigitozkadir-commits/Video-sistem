// PLACEHOLDER - replace by regenerating from measured audio once a project
// has real narration + assets. See scripts/generate_ryskulov_scenes_data.py
// or scripts/generate_avrasya_scenes_data.py for the pattern: it walks
// projects/<id>/scenes/SC-*.json, ffprobes each assets/audio/NAR-SC-*.wav
// for its real duration (narration is the clock - CLAUDE.md law #3, never
// hand-estimate once audio exists), collects assets/still|video/SC-*_imgN.*
// per scene, and writes this exact file shape. Copy that script to
// scripts/generate_<project_id>_scenes_data.py and adjust the project dir.
//
// audioFile may be null (e.g. a silent title card) - StudioComposition
// below already handles that case.
import type { Caption } from "@remotion/captions";

export interface SceneVisual {
  type: "video" | "still";
  file: string;
}

export interface SceneData {
  id: string;
  title: string;
  audioFile: string | null;
  visuals: SceneVisual[];
  startFrame: number;
  durationFrames: number;
  // Optional, opt-in (review finding B-05): per-scene word timing from
  // scripts/generate_captions.py's caption_track.schema.json output,
  // already shaped as @remotion/captions' own Caption[] type - no
  // transformation needed between the JSON file and this field. A scene
  // with no captions (undefined, or omitted entirely) renders exactly as
  // before - StudioComposition only renders the caption overlay when this
  // is present and non-empty.
  captions?: Caption[];
}

export const FPS = 30;

// Two placeholder scenes so `npx remotion studio` boots without a real
// project wired up yet. Replace entirely once scenesData.ts is regenerated.
export const SCENES: SceneData[] = [
  {
    id: "SC-001",
    title: "Placeholder scene - replace with real project data",
    audioFile: null,
    visuals: [],
    startFrame: 0,
    durationFrames: 90,
  },
];

export const TOTAL_FRAMES = SCENES.reduce((sum, s) => sum + s.durationFrames, 0);

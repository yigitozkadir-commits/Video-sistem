#!/usr/bin/env python3
"""
Incremental (scene-level) rendering for the atlas Remotion videos.

The full-video renders in this project take 5-20 minutes each because
Remotion re-renders every frame from scratch on every run, even when only
one scene's image or narration changed. Since each video is built from
independent <Sequence> scenes (remotion_atlas/src/compositions/
AtlasSceneRenderer.tsx), each scene can be rendered as its own short clip
and cached by a fingerprint of its actual inputs (image sha256 + audio
sha256 + timing). Re-running after changing one scene reuses every other
scene's cached clip and only re-renders the one that changed, then
re-concatenates - concatenation is a stream copy (no re-encode), so it's
seconds, not minutes.

Usage:
    python3 scripts/render_scene_clips.py <video_number>

Reads remotion_atlas/src/data/v<N>.json (written by
generate_atlas_scenes_data.py) for the scene list, composition id, and fps.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))
from production_ledger import ArtifactCache  # noqa: E402


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def render_clip(remotion_dir: Path, composition: str, start: int, end: int, out_path: Path) -> None:
    subprocess.run(
        ["npx", "remotion", "render", "src/index.ts", composition, str(out_path),
         f"--frames={start}-{end}", "--concurrency=4"],
        cwd=remotion_dir, check=True,
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
    )


def concat_clips(clip_paths: list[Path], out_path: Path) -> None:
    list_file = out_path.parent / f".{out_path.stem}_concat_list.txt"
    list_file.write_text("\n".join(f"file '{p.resolve()}'" for p in clip_paths))
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
         "-i", str(list_file), "-c", "copy", str(out_path)],
        check=True,
    )
    list_file.unlink()


def main():
    if len(sys.argv) != 2:
        print("Usage: render_scene_clips.py <video_number>")
        sys.exit(1)
    video_num = sys.argv[1]

    data_path = REPO_ROOT / "remotion_atlas" / "src" / "data" / f"v{video_num}.json"
    data = json.loads(data_path.read_text())
    composition = data["composition"]
    project = data["project"]
    remotion_dir = REPO_ROOT / data["remotion_dir"]
    scenes = data["scenes"]

    state_dir = REPO_ROOT / "projects" / project / "state"
    cache = ArtifactCache(state_dir, index_name="render_clip_cache_index.json")
    clips_dir = state_dir / "scene_clips" / composition
    clips_dir.mkdir(parents=True, exist_ok=True)

    clip_paths = []
    rendered_count = 0
    reused_count = 0

    for scene in scenes:
        visual_path = (remotion_dir / "public" / scene["visualFile"].replace("../public/", "")).resolve()
        audio_path = (remotion_dir / "public" / scene["audioFile"].replace("../public/", "")).resolve()

        fp = ArtifactCache.fingerprint(
            composition=composition,
            scene_id=scene["id"],
            visual_sha256=sha256_file(visual_path),
            audio_sha256=sha256_file(audio_path),
            start_frame=scene["startFrame"],
            duration_frames=scene["durationFrames"],
        )
        # Content-addressed filename: two different fingerprints must never
        # share a path, or reverting a scene's input would silently reuse a
        # stale clip left behind by the intermediate edit.
        cached_clip = cache.get(fp)
        if cached_clip is not None:
            print(f"  [cache hit] {scene['id']}")
            reused_count += 1
            clip_path = cached_clip
        else:
            clip_path = clips_dir / f"{scene['id']}-{fp[:16]}.mp4"
            start = scene["startFrame"]
            end = start + scene["durationFrames"] - 1
            print(f"  [rendering] {scene['id']} (frames {start}-{end})...")
            render_clip(remotion_dir, composition, start, end, clip_path)
            cache.put(fp, clip_path, scene_id=scene["id"])
            rendered_count += 1

        clip_paths.append(clip_path)

    print(f"\n{rendered_count} scene(s) rendered, {reused_count} reused from cache.")

    out_path = REPO_ROOT / "output" / f"{composition}.mp4"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Concatenating {len(clip_paths)} clips -> {out_path}")
    concat_clips(clip_paths, out_path)
    print(f"Done: {out_path}")


if __name__ == "__main__":
    main()

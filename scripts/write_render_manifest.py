#!/usr/bin/env python3
"""
Writes a schemas/render_manifest.schema.json-compliant record for a
finished Remotion render: sha256 of the output file, resolution, fps,
codec, timing, result. This is the "artifact registry" / deterministic
replay idea made concrete - answering `studio why <artifact>` from a
file instead of from memory.

Usage:
    python3 scripts/write_render_manifest.py \
        --output ../output/atlas-video-1.mp4 \
        --composition atlas-video-1 \
        --project PRJ-gok-umay-atlasi \
        --started 2026-08-06T10:11:00Z \
        --result success
"""
import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def ffprobe_video(path: Path) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,codec_name,r_frame_rate",
         "-show_entries", "format=duration",
         "-of", "json", str(path)],
        capture_output=True, text=True, check=True,
    ).stdout
    return json.loads(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True, help="Path to the rendered mp4")
    ap.add_argument("--composition", required=True)
    ap.add_argument("--project", required=True, help="Project ID, e.g. PRJ-gok-umay-atlasi")
    ap.add_argument("--started", required=True, help="ISO8601 start time")
    ap.add_argument("--result", default="success", choices=["success", "failed", "partial"])
    args = ap.parse_args()

    output_path = Path(args.output).resolve()
    probe = ffprobe_video(output_path)
    stream = probe["streams"][0]

    manifest = {
        "run_id": datetime.now(timezone.utc).strftime("RUN-%Y%m%dT%H%MZ"),
        "scope": "master",
        "target_id": args.composition,
        "composition": args.composition,
        "fps": round(eval(stream["r_frame_rate"])),
        "resolution": f"{stream['width']}x{stream['height']}",
        "codec": stream["codec_name"],
        "outputs": [{
            "path": str(output_path),
            "sha256": sha256_file(output_path),
            "bytes": output_path.stat().st_size,
        }],
        "started_at": args.started,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "result": args.result,
    }

    repo_root = Path(__file__).parent.parent
    state_dir = repo_root / "projects" / args.project / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = state_dir / "render_manifest.jsonl"
    with open(manifest_path, "a") as f:
        f.write(json.dumps(manifest, ensure_ascii=False) + "\n")

    print(f"Wrote manifest entry to {manifest_path}")
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

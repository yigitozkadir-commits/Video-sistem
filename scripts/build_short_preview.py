#!/usr/bin/env python3
"""Render a 9:16 short-cut preview from a state/short_edit.json manifest.

This is the cheap preview path, not the master path. It exists so a reels cut
can be judged as a *cut* -- pacing, shot order, whether the loop closes --
before any narration is bought (M16's pre_generation_approval gate) and before
a Remotion master render is scheduled.

Stills get their motion in the edit, not from Flow: a slow push-in, pull-out or
tilt-up, chosen per shot in the manifest. Video slots are trimmed from the
source clip, never looped -- the manifest is rejected if a slot is longer than
its clip (CLAUDE.md sec 10, the stutter-loop defect this studio has already
paid for once).

Usage:
    python3 scripts/build_short_preview.py <project_id> [--out PATH]
"""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lib.checklist_common import probe_duration  # noqa: E402

ZOOM = 1.06  # how far a still travels over its slot


def _run(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        sys.exit(f"ffmpeg failed:\n{' '.join(cmd)}\n{proc.stderr[-2000:]}")


def _still_filter(motion: str, frames: int, w: int, h: int) -> str:
    """zoompan expression for a still, sized to the target canvas."""
    over_w, over_h = w * 2, h * 2
    base = f"scale={over_w}:-2,crop={over_w}:{over_h},"
    x = "iw/2-(iw/zoom/2)"
    y = "ih/2-(ih/zoom/2)"
    if motion == "push_in":
        z = f"1+{ZOOM - 1:.4f}*on/{frames}"
    elif motion == "pull_out":
        z = f"{ZOOM:.4f}-{ZOOM - 1:.4f}*on/{frames}"
    elif motion == "tilt_up":
        z = f"{ZOOM:.4f}"
        y = f"(ih-ih/zoom)*(1-on/{frames})"
    elif motion == "static":
        z = "1"
    else:
        sys.exit(f"unknown motion: {motion}")
    return base + (
        f"zoompan=z='{z}':d=1:x='{x}':y='{y}':s={w}x{h}:fps=30,"
        f"setsar=1,format=yuv420p"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("project_id")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    proj = pathlib.Path("projects") / args.project_id
    manifest = json.loads((proj / "state" / "short_edit.json").read_text())
    w = manifest["canvas"]["width"]
    h = manifest["canvas"]["height"]
    fps = manifest["canvas"]["fps"]
    shots = manifest["shots"]

    # Preflight: a video slot must never outrun its source clip.
    for s in shots:
        if s["kind"] != "video":
            continue
        src = probe_duration(s["path"])
        if s["duration_s"] > src + 0.01:
            sys.exit(
                f"{s['shot_id']}: slot {s['duration_s']}s exceeds clip {src:.2f}s "
                "-- would loop. Shorten the slot or regenerate a longer clip."
            )

    out = pathlib.Path(
        args.out or proj / "output" / f"{args.project_id}_short_preview.mp4"
    )
    out.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = pathlib.Path(tmp)
        parts = []
        for s in shots:
            part = tmpdir / f"{s['shot_id']}.mp4"
            frames = round(s["duration_s"] * fps)
            if s["kind"] == "still":
                cmd = [
                    "ffmpeg", "-y", "-loglevel", "error",
                    "-loop", "1", "-framerate", str(fps), "-i", s["path"],
                    "-frames:v", str(frames),
                    "-vf", _still_filter(s["motion"], frames, w, h),
                ]
            else:
                cmd = [
                    "ffmpeg", "-y", "-loglevel", "error",
                    "-i", s["path"], "-frames:v", str(frames),
                    "-vf", (
                        f"scale={w}:{h}:force_original_aspect_ratio=increase,"
                        f"crop={w}:{h},fps={fps},setsar=1,format=yuv420p"
                    ),
                ]
            cmd += [
                "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                "-pix_fmt", "yuv420p", str(part),
            ]
            _run(cmd)
            parts.append(part)
            print(f"  {s['shot_id']}  {s['duration_s']:>4}s  {s['motion']}")

        listing = tmpdir / "concat.txt"
        listing.write_text("".join(f"file '{p}'\n" for p in parts))
        _run([
            "ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
            "-i", str(listing), "-c", "copy", str(out),
        ])

    actual = probe_duration(str(out))
    planned = manifest["total_duration_s"]
    print(f"\n{out}  {actual:.2f}s (planned {planned}s)")
    if abs(actual - planned) > 0.15:
        sys.exit(f"duration drift {actual - planned:+.2f}s -- investigate")


if __name__ == "__main__":
    main()

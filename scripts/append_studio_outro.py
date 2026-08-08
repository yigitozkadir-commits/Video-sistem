#!/usr/bin/env python3
"""
Appends the studio's signature closing (brand/GOKUMAY_signature_outro.mp4)
to the end of a finished master render. Mandatory final production step
for every video before Kaggle/YouTube delivery (CLAUDE.md law - see
"Signature outro" section).

The outro is a fixed 1176x784 @24fps clip - almost never a match for a
project's actual canvas (16:9 1920x1080, 9:16 1024x1536, etc). This script
scales it to fit inside the target canvas with letterboxing/pillarboxing
(never crops the logo) and matches fps before concatenating, so the same
outro file works unmodified across every project regardless of aspect
ratio.

Usage:
    python3 scripts/append_studio_outro.py <input_master.mp4> <output.mp4>
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
OUTRO_PATH = REPO_ROOT / "brand" / "GOKUMAY_signature_outro.mp4"


def probe(path: Path) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json",
         "-show_entries", "stream=width,height,r_frame_rate,codec_type",
         "-show_entries", "format=duration", str(path)],
        capture_output=True, text=True, check=True,
    ).stdout
    data = json.loads(out)
    video_stream = next(s for s in data["streams"] if s["codec_type"] == "video")
    return {
        "width": video_stream["width"],
        "height": video_stream["height"],
        "duration": float(data["format"]["duration"]),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input_master")
    ap.add_argument("output")
    args = ap.parse_args()

    src = Path(args.input_master)
    out = Path(args.output)
    if not src.exists():
        print(f"ERROR: {src} not found", file=sys.stderr)
        sys.exit(1)
    if not OUTRO_PATH.exists():
        print(f"ERROR: {OUTRO_PATH} not found", file=sys.stderr)
        sys.exit(1)

    target = probe(src)
    w, h = target["width"], target["height"]
    print(f"Target canvas: {w}x{h}, master duration {target['duration']:.2f}s")

    # Scale outro to fit inside target canvas preserving aspect ratio, pad
    # with black to fill exactly - never crops the logo, works for both
    # landscape and portrait targets from the same 1176x784 source.
    scale_pad = (
        f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
        f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black,setsar=1,fps=30"
    )

    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-i", str(src),
        "-i", str(OUTRO_PATH),
        "-filter_complex",
        f"[1:v]{scale_pad}[outro_v];"
        f"[0:v][0:a][outro_v][1:a]concat=n=2:v=1:a=1[outv][outa]",
        "-map", "[outv]", "-map", "[outa]",
        "-c:v", "libx264", "-crf", "18", "-preset", "medium",
        "-c:a", "aac", "-b:a", "192k",
        str(out),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("ERROR: ffmpeg failed:\n" + r.stderr, file=sys.stderr)
        sys.exit(1)

    result = probe(out)
    expected_min = target["duration"] + 6.5  # outro is 7.04s, allow fps-conversion slack
    if result["duration"] < expected_min:
        print(
            f"ERROR: output duration {result['duration']:.2f}s is shorter than "
            f"expected (master + outro >= {expected_min:.2f}s) - outro may not "
            f"have been appended correctly, NOT declaring success.",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"OK: {out} ({result['width']}x{result['height']}, {result['duration']:.2f}s)")


if __name__ == "__main__":
    main()

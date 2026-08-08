#!/usr/bin/env python3
"""
Populates schemas/asset_manifest.schema.json for a project: hashes and
type-classifies every real production asset (stills, narration audio,
reference video, and delivered output renders), so `studio why <artifact>`
can be answered by reading a file instead of re-deriving it by hand.

This is the concrete scope of the "Knowledge Graph & Asset Registry" idea
from the uploaded Sandrex docs: those docs describe a graph database with
registerAsset()/resolveDependencies()/findAffectedAssets() APIs. This repo
has ~170 assets across two projects and a schema that already models them
flatly (asset -> optional scene_reference); a graph engine has no query
this flat form can't already answer, so this script writes the flat form.

Re-running any operation must be a no-op (CLAUDE.md hard rule): re-running
this script reuses sha256 already computed in render_manifest.jsonl and the
audio/clip cache indexes rather than re-hashing large files, and produces
byte-identical `assets` content when nothing on disk changed (only
`generated_at` differs).

Usage:
    python3 scripts/write_asset_manifest.py [PRJ-id]   # default: all projects
"""
import glob
import hashlib
import json
import mimetypes
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

ASSET_TYPE_DIRS = {
    "still": "image",
    "image": "image",
    "reference": "image",
    "audio": "audio",
    "video": "video",
}

TYPE_CODE = {"image": "IMG", "audio": "AUD", "video": "VID"}

SCENE_ID_RE = re.compile(r"(SC-\d{3})")

# Final delivered renders live in the shared output/ dir, not a project
# subfolder, so the project -> filename mapping has to be explicit -
# render_manifest.jsonl records the same composition -> output/<file>
# association per render.
PROJECT_OUTPUTS = {
    "PRJ-daglar-uyuyan-devleri": ["output/master_final.mp4"],
    "PRJ-gok-umay-atlasi": [f"output/atlas-video-{n}.mp4" for n in range(1, 7)],
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_known_sha256(project_dir: Path) -> dict[str, str]:
    """resolved-path -> sha256, harvested from artifacts this repo already
    fingerprints, so files already hashed elsewhere aren't re-hashed here."""
    known = {}
    rm = project_dir / "state" / "render_manifest.jsonl"
    if rm.exists():
        for line in rm.read_text().splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            for o in row.get("outputs", []):
                # Path.__truediv__ discards the left side when the right is
                # already absolute, so this handles both relative and
                # absolute recorded paths without a branch.
                known[str((REPO_ROOT / o["path"]).resolve())] = o["sha256"]
    for idx_name in ("audio_cache_index.json", "scene_clip_cache_index.json"):
        idx_path = project_dir / "state" / idx_name
        if idx_path.exists():
            for entry in json.loads(idx_path.read_text()).values():
                known[str(Path(entry["path"]).resolve())] = entry["sha256"]
    return known


def ffprobe_duration(path: Path) -> float | None:
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True, check=True,
        )
        return round(float(out.stdout.strip()), 3)
    except Exception:
        return None


def ffprobe_video_size(path: Path) -> tuple[int, int] | tuple[None, None]:
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height", "-of", "json", str(path)],
            capture_output=True, text=True, check=True,
        )
        s = json.loads(out.stdout)["streams"][0]
        return s["width"], s["height"]
    except Exception:
        return None, None


def image_size(path: Path) -> tuple[int, int] | tuple[None, None]:
    try:
        from PIL import Image
        with Image.open(path) as im:
            return im.width, im.height
    except Exception:
        return None, None


def scene_reference(stem: str) -> str | None:
    m = SCENE_ID_RE.search(stem)
    return m.group(1) if m else None


def load_flow_generation_metadata(project_dir: Path) -> dict[str, dict[str, dict]]:
    """scene_id -> {"image": {...}, "video": {...}} from prompts_used/SH-NNN-01/
    {image,video}.json, so AI-generated assets carry their real seed/prompt_version
    instead of asset_manifest guessing at generation provenance."""
    out: dict[str, dict[str, dict]] = {}
    for shot_dir in sorted((project_dir / "prompts_used").glob("SH-*")):
        m = re.match(r"SH-(\d{3})-\d{2}", shot_dir.name)
        if not m:
            continue
        sid = f"SC-{m.group(1)}"
        for kind in ("image", "video"):
            p = shot_dir / f"{kind}.json"
            if p.exists():
                out.setdefault(sid, {})[kind] = json.loads(p.read_text())
    return out


# Filename suffix -> (creator_agent, disposition, is_ai_generated). Suffix is
# matched against the file stem (name without extension) via endswith().
ASSET_PROVENANCE_SUFFIXES = [
    ("_flow_alt", "visual", "REFERENCE_ONLY", True),
    ("_flow", "visual", "HERO_ASSET", True),
    ("_commons_flowupload", "technical", "ARCHIVE", False),
    ("_commons", "technical", "HERO_ASSET", False),
]


def build_manifest(project_id: str) -> tuple[Path, int]:
    project_dir = REPO_ROOT / "projects" / project_id
    known_sha = load_known_sha256(project_dir)
    flow_meta = load_flow_generation_metadata(project_dir)
    assets = []
    counters = {"IMG": 0, "AUD": 0, "VID": 0}

    def add(path: Path, asset_type: str) -> None:
        type_code = TYPE_CODE[asset_type]
        counters[type_code] += 1
        resolved = str(path.resolve())
        sha = known_sha.get(resolved) or sha256_file(path)
        entry = {
            "asset_id": f"AST-{type_code}-{counters[type_code]:06d}",
            "asset_type": asset_type,
            "path": str(path.relative_to(REPO_ROOT)),
            "mime_type": mimetypes.guess_type(str(path))[0] or "application/octet-stream",
            "sha256": sha,
            "bytes": path.stat().st_size,
            "created_at": datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(),
        }
        if asset_type == "image":
            w, h = image_size(path)
            if w:
                entry["width"], entry["height"] = w, h
        elif asset_type in ("audio", "video"):
            dur = ffprobe_duration(path)
            if dur is not None:
                entry["duration_s"] = dur
            if asset_type == "video":
                w, h = ffprobe_video_size(path)
                if w:
                    entry["width"], entry["height"] = w, h
        ref = scene_reference(path.stem)
        if ref:
            entry["scene_reference"] = ref
            for suffix, creator_agent, disposition, is_ai in ASSET_PROVENANCE_SUFFIXES:
                if path.stem.endswith(suffix):
                    entry["creator_agent"] = creator_agent
                    entry["disposition"] = disposition
                    if is_ai:
                        kind = "video" if asset_type == "video" else "image"
                        req = flow_meta.get(ref, {}).get(kind)
                        if req:
                            entry["generation"] = {
                                "model": req.get("model", "google_flow"),
                                "seed": req.get("seed"),
                                "prompt_version": req.get("prompt_version"),
                            }
                    break
        assets.append(entry)

    for sub, asset_type in ASSET_TYPE_DIRS.items():
        for p in sorted((project_dir / "assets" / sub).glob("*")):
            if p.is_file():
                add(p, asset_type)

    for rel in PROJECT_OUTPUTS.get(project_id, []):
        p = REPO_ROOT / rel
        if p.is_file():
            add(p, "video")

    manifest = {
        "project_id": project_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "assets": assets,
    }
    out_path = project_dir / "state" / "asset_manifest.json"
    out_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    return out_path, len(assets)


def main() -> None:
    if len(sys.argv) > 1:
        targets = [sys.argv[1]]
    else:
        targets = sorted(
            Path(p).name for p in glob.glob(str(REPO_ROOT / "projects" / "PRJ-*"))
        )
    for pid in targets:
        out_path, n = build_manifest(pid)
        print(f"{pid}: {n} assets -> {out_path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()

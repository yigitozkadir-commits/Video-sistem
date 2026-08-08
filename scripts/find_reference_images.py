#!/usr/bin/env python3
"""
Searches Wikimedia Commons for real, reusably-licensed reference images per
scene, instead of defaulting every still to AI generation. Only Public
Domain / CC0 / CC-BY / CC-BY-SA results are accepted - anything
non-commercial (NC), no-derivatives (ND), or with an unclear/missing
license is rejected outright, never downloaded.

Ownership split (CLAUDE.md law #2, Single Writer): scripts/
scaffold_baskurtlar_project.py owns scenes/*.json (the plan) and never
touches this script's output; this script owns
state/reference_image_sources.jsonl (the resolution) and never edits
scenes/*.json. Join the two by scene_id/shot_id when you need "what did
this scene end up using."

Uses curl (not Python's http stack) against the Wikimedia Commons API -
this repo's egress proxy setup is already verified working with curl +
the CA bundle (see /root/.ccr/README.md); this avoids re-solving that for
a second HTTP client.

Usage:
    python3 scripts/find_reference_images.py [PRJ-id]   # default: PRJ-baskurtlar-arastirma
"""
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
CA_BUNDLE = "/root/.ccr/ca-bundle.crt"
API = "https://commons.wikimedia.org/w/api.php"

ALLOWED_LICENSE_PREFIXES = ("cc0", "cc by", "public domain", "pd-")
REJECTED_LICENSE_MARKERS = ("nc", "nd")  # substrings checked on normalized shortname tokens
MIN_WIDTH = 1000
CANDIDATES_TO_CHECK = 6


def curl_json(params: dict) -> dict:
    from urllib.parse import quote
    url = API + "?" + "&".join(f"{k}={quote(str(v), safe='|')}" for k, v in params.items())
    out = subprocess.run(
        ["curl", "-sS", "--cacert", CA_BUNDLE, "-A", "PRJ-baskurtlar-arastirma-research/1.0", url],
        capture_output=True, text=True, check=True, timeout=30,
    )
    try:
        return json.loads(out.stdout)
    except json.JSONDecodeError:
        return {}


def search_candidates(query: str, limit: int = CANDIDATES_TO_CHECK) -> list[str]:
    data = curl_json({
        "action": "query", "list": "search", "srsearch": query,
        "srnamespace": "6", "format": "json", "srlimit": str(limit),
    })
    return [r["title"] for r in data.get("query", {}).get("search", [])]


def license_is_reusable(short_name: str) -> bool:
    s = short_name.lower().strip()
    if any(marker in s.split() for marker in REJECTED_LICENSE_MARKERS):
        return False
    if "-nc" in s or "-nd" in s or "noncommercial" in s or "no derivative" in s:
        return False
    return s.startswith(ALLOWED_LICENSE_PREFIXES)


def get_imageinfo(title: str) -> dict | None:
    data = curl_json({
        "action": "query", "titles": title,
        "prop": "imageinfo", "iiprop": "url|extmetadata|size|mime",
        "format": "json",
    })
    pages = data.get("query", {}).get("pages", {})
    for page in pages.values():
        info = (page.get("imageinfo") or [None])[0]
        return info
    return None


MIME_EXT = {
    "image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp",
    "image/tiff": ".tiff", "image/gif": ".gif",
    "video/mp4": ".mp4", "video/webm": ".webm", "video/ogg": ".ogv",
}


def find_best_candidate(query: str) -> dict | None:
    for title in search_candidates(query):
        info = get_imageinfo(title)
        if not info:
            continue
        mime = info.get("mime", "")
        if mime not in MIME_EXT:
            continue  # reject PDFs, DjVu, audio, etc. - only real images/video are usable visuals
        meta = info.get("extmetadata", {})
        license_short = meta.get("LicenseShortName", {}).get("value", "")
        if not license_short or not license_is_reusable(license_short):
            continue
        if info.get("width", 0) < MIN_WIDTH:
            continue
        return {
            "title": title,
            "url": info["url"],
            "mime": info.get("mime", ""),
            "width": info.get("width"),
            "height": info.get("height"),
            "license_short": license_short,
            "license_url": meta.get("LicenseUrl", {}).get("value", ""),
            "artist": _strip_html(meta.get("Artist", {}).get("value", "")),
            "credit": _strip_html(meta.get("Credit", {}).get("value", "")),
            "description_url": info.get("descriptionurl", ""),
        }
    return None


def _strip_html(s: str) -> str:
    import re
    return re.sub(r"<[^>]+>", "", s).strip()


def download(url: str, dest: Path) -> int:
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["curl", "-sS", "--cacert", CA_BUNDLE, "-A", "PRJ-baskurtlar-arastirma-research/1.0",
         "-o", str(dest), url],
        check=True, timeout=60,
    )
    return dest.stat().st_size


def sha256_file(path: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    project_id = sys.argv[1] if len(sys.argv) > 1 else "PRJ-baskurtlar-arastirma"
    project_dir = REPO_ROOT / "projects" / project_id
    state_dir = project_dir / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    log_path = state_dir / "reference_image_sources.jsonl"

    resolved = 0
    skipped_ai_required = 0
    no_candidate = 0

    with open(log_path, "a") as log:
        for scene_path in sorted((project_dir / "scenes").glob("SC-*.json")):
            scene = json.loads(scene_path.read_text())
            if scene.get("ai_required"):
                skipped_ai_required += 1
                continue
            keywords = scene.get("search_keywords")
            if not keywords or scene.get("visual_decision") == "reuse":
                continue

            print(f"searching: {scene['scene_id']} — {keywords!r}")
            best = find_best_candidate(keywords)
            if not best:
                print(f"  no reusably-licensed candidate found (>= {MIN_WIDTH}px, PD/CC0/CC-BY/CC-BY-SA)")
                no_candidate += 1
                continue

            ext = MIME_EXT.get(best["mime"], ".jpg")
            dest_subdir = "video" if best["mime"].startswith("video") else "still"
            dest = project_dir / "assets" / dest_subdir / f"{scene['scene_id']}_commons{ext}"
            size_bytes = download(best["url"], dest)
            sha = sha256_file(dest)

            record = {
                "scene_id": scene["scene_id"],
                "shot_id": (scene.get("shots") or [None])[0],
                "query": keywords,
                "commons_title": best["title"],
                "source_url": best["description_url"],
                "file_url": best["url"],
                "license": best["license_short"],
                "license_url": best["license_url"],
                "attribution": best["artist"] or best["credit"],
                "local_path": str(dest.relative_to(REPO_ROOT)),
                "bytes": size_bytes,
                "sha256": sha,
                "width": best["width"],
                "height": best["height"],
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
            }
            log.write(json.dumps(record, ensure_ascii=False) + "\n")
            log.flush()
            print(f"  found: {best['title']} ({best['license_short']}) -> {dest.relative_to(REPO_ROOT)}")
            resolved += 1

    print()
    print(f"Resolved with real images: {resolved}")
    print(f"No reusable candidate found (Flow prompt remains the fallback): {no_candidate}")
    print(f"Skipped (ai_required, e.g. mythological content): {skipped_ai_required}")
    print(f"Log: {log_path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()

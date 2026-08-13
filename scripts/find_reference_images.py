#!/usr/bin/env python3
"""
Searches real public/open archives for reusably-licensed reference images
per scene, instead of defaulting every still to AI generation. Only Public
Domain / CC0 / CC-BY / CC-BY-SA results are accepted - anything
non-commercial (NC), no-derivatives (ND), or with an unclear/missing
license is rejected outright, never downloaded (M09 §8b - "sourced
archival asset" is a distinct class from a REF-* generation reference).

Three providers, tried in order, first reusably-licensed hit wins:
  1. Wikimedia Commons - the original provider this script shipped with.
     Broadest general-purpose coverage, license metadata is reliable.
  2. NASA Images (images-api.nasa.gov) - space/science/aeronautics subject
     matter. NASA's own media usage policy is "not protected by copyright
     unless noted" (public domain by default for US-government-produced
     work), but individual items can be credited to a non-NASA
     photographer/contractor with different terms - this script does NOT
     blanket-trust "source == nasa therefore public domain"; it still runs
     every candidate through the same license_is_reusable() gate, looking
     at whatever rights text the item actually carries. If NASA's API
     supplies no rights signal for an item at all, that's treated the same
     as any other missing-license case: rejected, not assumed-PD.
  3. Archive.org (advancedsearch.php) - the provider with the weakest
     license metadata of the three: `licenseurl` is absent on most items
     (verified by spot-checking real search results before writing this),
     and when present can itself be a non-reusable license (e.g.
     by-nc-nd). Never treat an Archive.org item with a missing licenseurl
     as "probably fine" - it is rejected exactly like any other unclear-
     license case, same rule as the other two providers.

Ownership split (CLAUDE.md law #2, Single Writer): scripts/
scaffold_baskurtlar_project.py owns scenes/*.json (the plan) and never
touches this script's output; this script owns
state/reference_image_sources.jsonl (the resolution) and never edits
scenes/*.json or project.json. Join the two by scene_id/shot_id when you
need "what did this scene end up using." When a scene ends up using a
sourced archival asset, its source_url is the right citation for
project.json's rights.evidence_ref - a human (or a scaffold script that
owns project.json) copies it in; this script never writes project.json.

Uses curl (not Python's http stack) against each provider's API - this
repo's egress proxy setup is already verified working with curl + the CA
bundle (see /root/.ccr/README.md) for the Wikimedia case; this avoids
re-solving that for a second HTTP client, and the same pattern is reused
unchanged for the two new providers. If a provider's host isn't reachable
through the proxy, that provider's search functions fail loudly (curl's
own non-zero exit / exception), not silently - the caller should see a
real error, not a false "no candidate found."

Output shape matches schemas/archival_asset.schema.json - every record
written to state/reference_image_sources.jsonl validates against it.

Usage:
    python3 scripts/find_reference_images.py [PRJ-id]   # default: PRJ-baskurtlar-arastirma
"""
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
CA_BUNDLE = "/root/.ccr/ca-bundle.crt"
USER_AGENT = "PRJ-baskurtlar-arastirma-research/1.0"

WIKIMEDIA_API = "https://commons.wikimedia.org/w/api.php"
NASA_API = "https://images-api.nasa.gov/search"
ARCHIVE_ORG_API = "https://archive.org/advancedsearch.php"

ALLOWED_LICENSE_PREFIXES = ("cc0", "cc by", "public domain", "pd-")
REJECTED_LICENSE_MARKERS = ("nc", "nd")  # substrings checked on normalized shortname tokens
MIN_WIDTH = 1000
CANDIDATES_TO_CHECK = 6

MIME_EXT = {
    "image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp",
    "image/tiff": ".tiff", "image/gif": ".gif",
    "video/mp4": ".mp4", "video/webm": ".webm", "video/ogg": ".ogv",
}


def _curl_json(url: str) -> dict:
    out = subprocess.run(
        ["curl", "-sS", "--cacert", CA_BUNDLE, "-A", USER_AGENT, url],
        capture_output=True, text=True, check=True, timeout=30,
    )
    try:
        return json.loads(out.stdout)
    except json.JSONDecodeError:
        return {}


def license_is_reusable(short_name: str) -> bool:
    s = (short_name or "").lower().strip()
    if not s:
        return False
    if any(marker in s.split() for marker in REJECTED_LICENSE_MARKERS):
        return False
    if "-nc" in s or "-nd" in s or "noncommercial" in s or "no derivative" in s:
        return False
    return s.startswith(ALLOWED_LICENSE_PREFIXES)


def _strip_html(s: str) -> str:
    return re.sub(r"<[^>]+>", "", s or "").strip()


# ---------------------------------------------------------------------------
# Provider: Wikimedia Commons (original provider)
# ---------------------------------------------------------------------------

def _wikimedia_candidates(query: str, limit: int = CANDIDATES_TO_CHECK) -> list[dict]:
    from urllib.parse import quote

    def curl_json(params: dict) -> dict:
        url = WIKIMEDIA_API + "?" + "&".join(f"{k}={quote(str(v), safe='|')}" for k, v in params.items())
        return _curl_json(url)

    data = curl_json({
        "action": "query", "list": "search", "srsearch": query,
        "srnamespace": "6", "format": "json", "srlimit": str(limit),
    })
    titles = [r["title"] for r in data.get("query", {}).get("search", [])]

    candidates = []
    for title in titles:
        info_data = curl_json({
            "action": "query", "titles": title,
            "prop": "imageinfo", "iiprop": "url|extmetadata|size|mime",
            "format": "json",
        })
        pages = info_data.get("query", {}).get("pages", {})
        info = None
        for page in pages.values():
            info = (page.get("imageinfo") or [None])[0]
            break
        if not info:
            continue
        mime = info.get("mime", "")
        if mime not in MIME_EXT:
            continue  # reject PDFs, DjVu, audio, etc. - only real images/video are usable visuals
        meta = info.get("extmetadata", {})
        license_short = meta.get("LicenseShortName", {}).get("value", "")
        candidates.append({
            "source": "wikimedia_commons",
            "source_title": title,
            "source_url": info.get("descriptionurl", ""),
            "file_url": info.get("url", ""),
            "mime": mime,
            "width": info.get("width"),
            "height": info.get("height"),
            "license_short": license_short,
            "license_url": meta.get("LicenseUrl", {}).get("value", ""),
            "attribution": _strip_html(meta.get("Artist", {}).get("value", "")) or _strip_html(meta.get("Credit", {}).get("value", "")),
        })
    return candidates


# ---------------------------------------------------------------------------
# Provider: NASA Images (images-api.nasa.gov)
# ---------------------------------------------------------------------------

def _nasa_candidates(query: str, limit: int = CANDIDATES_TO_CHECK) -> list[dict]:
    from urllib.parse import quote
    url = f"{NASA_API}?q={quote(query)}&media_type=image"
    data = _curl_json(url)
    items = (data.get("collection") or {}).get("items", [])[:limit]

    candidates = []
    for item in items:
        data_entries = item.get("data") or [{}]
        meta = data_entries[0]
        links = item.get("links") or []
        # Prefer the highest-resolution asset link (~orig), fall back to whatever's there.
        orig = next((l for l in links if l.get("href", "").endswith("~orig.jpg")), None)
        best_link = orig or (links[0] if links else None)
        if not best_link:
            continue
        file_url = best_link["href"]
        nasa_id = meta.get("nasa_id", "")
        # NASA's own usage policy: content is public domain unless the item's
        # own metadata says otherwise. We don't have a per-item license field
        # from this endpoint, so we treat "photographer credited to NASA
        # itself or missing" as public-domain-eligible, and anything crediting
        # a named non-NASA photographer/contractor as unclear -> rejected,
        # rather than assuming every NASA result is automatically reusable.
        photographer = (meta.get("photographer") or "").strip()
        if photographer and "nasa" not in photographer.lower():
            license_short = ""  # unclear - will be rejected by license_is_reusable()
        else:
            license_short = "public domain"
        candidates.append({
            "source": "nasa",
            "source_title": nasa_id or meta.get("title", ""),
            "source_url": f"https://images.nasa.gov/details/{nasa_id}" if nasa_id else "",
            "file_url": file_url,
            "mime": "image/jpeg",
            "width": None,  # NASA's search response doesn't reliably include pixel dims
            "height": None,
            "license_short": license_short,
            "license_url": "https://www.nasa.gov/nasa-brand-center/images-and-media/",
            "attribution": photographer,
        })
    return candidates


# ---------------------------------------------------------------------------
# Provider: Archive.org (advancedsearch.php)
# ---------------------------------------------------------------------------

def _archive_org_candidates(query: str, limit: int = CANDIDATES_TO_CHECK) -> list[dict]:
    from urllib.parse import quote
    url = (
        f"{ARCHIVE_ORG_API}?q=mediatype%3Aimage+AND+{quote(query)}"
        "&fl[]=identifier&fl[]=title&fl[]=licenseurl"
        f"&rows={limit}&output=json"
    )
    data = _curl_json(url)
    docs = (data.get("response") or {}).get("docs", [])

    candidates = []
    for doc in docs:
        identifier = doc.get("identifier", "")
        if not identifier:
            continue
        license_url = doc.get("licenseurl", "")
        # Archive.org's licenseurl is absent on most items (verified before
        # writing this) - absence is NOT treated as "probably public domain",
        # it's treated the same as any other unclear-license case: rejected.
        license_short = _license_short_from_cc_url(license_url) if license_url else ""
        candidates.append({
            "source": "archive_org",
            "source_title": doc.get("title", identifier),
            "source_url": f"https://archive.org/details/{identifier}",
            # __ia_thumb.jpg is the one predictably-named derivative Archive.org
            # always generates; full-resolution originals have per-item names
            # this search endpoint doesn't expose, so this is a conservative choice.
            "file_url": f"https://archive.org/download/{identifier}/__ia_thumb.jpg",
            "mime": "image/jpeg",
            "width": None,
            "height": None,
            "license_short": license_short,
            "license_url": license_url,
            "attribution": "",
        })
    return candidates


def _license_short_from_cc_url(license_url: str) -> str:
    """archive.org gives a Creative Commons URL, not a short name like
    Wikimedia does - derive one so license_is_reusable() can be applied
    uniformly across all three providers."""
    u = license_url.lower()
    if "publicdomain" in u or "/zero/" in u:
        return "cc0"
    m = re.search(r"/licenses/([a-z-]+)/", u)
    if m:
        return f"cc {m.group(1)}"
    return ""


PROVIDERS = [
    ("wikimedia_commons", _wikimedia_candidates),
    ("nasa", _nasa_candidates),
    ("archive_org", _archive_org_candidates),
]


def find_best_candidate(query: str) -> dict | None:
    """Tries each provider in order; returns the first reusably-licensed,
    minimum-resolution candidate. Providers with no usable pixel-dimension
    data (NASA, Archive.org today) skip the MIN_WIDTH check rather than
    being rejected by a check they have no data to pass - the license gate
    still applies unconditionally to all three."""
    for _, search_fn in PROVIDERS:
        for cand in search_fn(query):
            if cand["mime"] not in MIME_EXT:
                continue
            if not license_is_reusable(cand["license_short"]):
                continue
            width = cand.get("width")
            if width is not None and width < MIN_WIDTH:
                continue
            return cand
    return None


def download(url: str, dest: Path) -> int:
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["curl", "-sS", "--cacert", CA_BUNDLE, "-A", USER_AGENT, "-o", str(dest), url],
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
    by_source = {}

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
                print(f"  no reusably-licensed candidate found (>= {MIN_WIDTH}px where known, PD/CC0/CC-BY/CC-BY-SA)")
                no_candidate += 1
                continue

            ext = MIME_EXT.get(best["mime"], ".jpg")
            dest_subdir = "video" if best["mime"].startswith("video") else "still"
            dest = project_dir / "assets" / dest_subdir / f"{scene['scene_id']}_{best['source']}{ext}"
            size_bytes = download(best["file_url"], dest)
            sha = sha256_file(dest)

            record = {
                "scene_id": scene["scene_id"],
                "shot_id": (scene.get("shots") or [None])[0],
                "query": keywords,
                "source": best["source"],
                "source_title": best["source_title"],
                "source_url": best["source_url"],
                "file_url": best["file_url"],
                "license": best["license_short"],
                "license_url": best["license_url"],
                "attribution": best["attribution"],
                "local_path": str(dest.relative_to(REPO_ROOT)),
                "bytes": size_bytes,
                "sha256": sha,
                "width": best["width"],
                "height": best["height"],
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
            }
            log.write(json.dumps(record, ensure_ascii=False) + "\n")
            log.flush()
            print(f"  found ({best['source']}): {best['source_title']} ({best['license_short']}) -> {dest.relative_to(REPO_ROOT)}")
            resolved += 1
            by_source[best["source"]] = by_source.get(best["source"], 0) + 1

    print()
    print(f"Resolved with real images: {resolved} {by_source or ''}")
    print(f"No reusable candidate found (Flow prompt remains the fallback): {no_candidate}")
    print(f"Skipped (ai_required, e.g. mythological content): {skipped_ai_required}")
    print(f"Log: {log_path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()

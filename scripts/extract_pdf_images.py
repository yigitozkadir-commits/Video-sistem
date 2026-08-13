#!/usr/bin/env python3
"""
First code implementation of bible/Module_14_Claude_Code_Enterprise.md §5
"IMAGE PIPELINE" and Module_22_Scene_Planning_Algorithm.md §6d: extracts every
meaningful embedded raster image from a source PDF, applies a crude automatic
pre-classification (M14 §5.1 taxonomy), and writes state/image_catalog.json
per schemas/image_catalog.schema.json.

This is a PRE-FILTER, not a final classification. Every image is written with
needs_human_classification: true - CLAUDE.md §3 lets this agent decide image
classification/disposition, but a heuristic guess from width/height/aspect
ratio alone is not that decision. A human (or a later, deliberate Claude
pass) still reviews and locks in class/disposition/rationale per image.

Never opens each extracted image with the Read tool - PIL dimension/integrity
checks only, per the "stop reading every image visually" optimization rule
established this session. Spot-check 1-2 samples manually if something looks
structurally wrong (crash, all-zero dimensions, etc), not every image.

Usage:
    python3 scripts/extract_pdf_images.py <pdf_path> <project_id>

Writes:
    projects/<project_id>/assets/reference/_source/<pdf_stem>.pdf   (archived copy)
    projects/<project_id>/assets/still/pdfimg/AST-IMG-NNNNNN.png    (extracted images)
    projects/<project_id>/state/image_catalog.json                 (appended, schema-validated shape)
"""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).parent.parent

EMBEDDED_IMAGE_MIN_PX = 100  # Module 22 §6d - filter out smask/decoration slivers
DECORATION_MAX_PX = 150      # below this on both dimensions -> decoration, not content


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def list_embedded_images(pdf_path: Path) -> list[dict]:
    """Parses `pdfimages -list` output into per-object records, in the same
    order pdfimages -png names its output files (out-000.png, out-001.png, ...)."""
    out = subprocess.run(
        ["pdfimages", "-list", str(pdf_path)], capture_output=True, text=True
    ).stdout
    records = []
    for line in out.splitlines()[2:]:
        parts = line.split()
        if len(parts) < 5:
            continue
        try:
            page, num = int(parts[0]), int(parts[1])
            img_type = parts[2]
            width, height = int(parts[3]), int(parts[4])
        except (ValueError, IndexError):
            continue
        records.append({"page": page, "num": num, "type": img_type, "width": width, "height": height})
    return records


def classify_heuristic(page: int, width: int, height: int, total_pages: int) -> str:
    """M14 §5.1 taxonomy. Crude size/aspect guess only - see module docstring."""
    if width < DECORATION_MAX_PX and height < DECORATION_MAX_PX:
        return "decoration"
    aspect = height / max(1, width)
    if page == 1 and width > 600:
        return "cover"
    if 1.3 <= aspect <= 2.2 and width > 400:
        return "portrait"
    if aspect > 2.5 or (1 / aspect) > 2.5:
        return "decoration"  # long thin strips - borders, ornaments
    return "illustration"


def next_asset_counter(image_catalog_path: Path, asset_manifest_path: Path) -> int:
    """Scans BOTH image_catalog.json and asset_manifest.json for the current
    max AST-IMG-* number - a project's asset_id space is shared across every
    registry that writes into it, not just this script's own output file.
    (Caught the hard way: a first pass here only checked image_catalog.json
    and collided with AST-IMG-000001..59 already assigned in asset_manifest.json
    to unrelated, previously-curated PNGs.)"""
    n = 0
    for path, key in ((image_catalog_path, "images"), (asset_manifest_path, "assets")):
        if not path.exists():
            continue
        for row in json.loads(path.read_text()).get(key, []):
            aid = row.get("asset_id", "")
            if aid.startswith("AST-IMG-"):
                n = max(n, int(aid.rsplit("-", 1)[1]))
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf_path")
    ap.add_argument("project_id")
    args = ap.parse_args()

    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        print(f"ERROR: {pdf_path} not found", file=sys.stderr)
        sys.exit(1)

    project_dir = REPO_ROOT / "projects" / args.project_id
    if not project_dir.exists():
        print(f"ERROR: {project_dir} not found - project must already exist", file=sys.stderr)
        sys.exit(1)

    source_dir = project_dir / "assets" / "reference" / "_source"
    still_dir = project_dir / "assets" / "still" / "pdfimg"
    state_dir = project_dir / "state"
    for d in (source_dir, still_dir, state_dir):
        d.mkdir(parents=True, exist_ok=True)

    # Archive the source PDF (never delete/skip provenance, CLAUDE.md).
    archived_pdf = source_dir / pdf_path.name
    if not archived_pdf.exists():
        shutil.copy2(pdf_path, archived_pdf)
    pdf_sha256 = sha256_file(pdf_path)

    pageinfo = subprocess.run(["pdfinfo", str(pdf_path)], capture_output=True, text=True).stdout
    total_pages = 1
    for line in pageinfo.splitlines():
        if line.startswith("Pages:"):
            total_pages = int(line.split()[-1])

    records = list_embedded_images(pdf_path)
    meaningful = [
        r for r in records
        if r["type"] != "smask" and r["width"] >= EMBEDDED_IMAGE_MIN_PX and r["height"] >= EMBEDDED_IMAGE_MIN_PX
    ]
    print(f"{len(records)} embedded objects total, {len(meaningful)} meaningful (non-smask, "
          f">= {EMBEDDED_IMAGE_MIN_PX}px both dims).")

    image_catalog_path = state_dir / "image_catalog.json"
    asset_manifest_path = state_dir / "asset_manifest.json"
    asset_n = next_asset_counter(image_catalog_path, asset_manifest_path)

    with tempfile.TemporaryDirectory() as tmpdir:
        prefix = Path(tmpdir) / "out"
        subprocess.run(["pdfimages", "-png", str(pdf_path), str(prefix)], capture_output=True)

        new_entries = []
        class_counts: dict[str, int] = {}
        for r in meaningful:
            src_file = Path(tmpdir) / f"out-{r['num']:03d}.png"
            if not src_file.exists():
                continue  # pdfimages couldn't render this object as PNG (rare, e.g. CMYK edge case)

            try:
                with Image.open(src_file) as im:
                    real_w, real_h = im.size
                    im.verify()
            except Exception as e:
                print(f"  SKIP page {r['page']} num {r['num']}: PIL could not open/verify ({e})", file=sys.stderr)
                continue

            asset_n += 1
            asset_id = f"AST-IMG-{asset_n:06d}"
            out_path = still_dir / f"{asset_id}.png"
            shutil.copy2(src_file, out_path)

            cls = classify_heuristic(r["page"], real_w, real_h, total_pages)
            class_counts[cls] = class_counts.get(cls, 0) + 1

            new_entries.append({
                "asset_id": asset_id,
                "page": r["page"],
                "px": [real_w, real_h],
                "mime": "image/png",
                "sha256": sha256_file(out_path),
                "class": cls,
                "scores": {
                    "narrative_relevance": 50, "visual_quality": 50, "resolution_adequacy": 50,
                },
                "disposition": "REFERENCE_ONLY",
                "rationale": (
                    f"scripts/extract_pdf_images.py ile {pdf_path.name} sayfa {r['page']}'den "
                    f"otomatik cikarildi. Kaba boyut/en-boy sezgisel siniflandirma ({cls}), "
                    f"insan/Claude gozden gecirmesi henuz yapilmadi."
                ),
                "needs_human_classification": True,
                "derived_from_pdf_sha256": pdf_sha256,
            })

    existing_images = []
    if image_catalog_path.exists():
        existing_images = json.loads(image_catalog_path.read_text()).get("images", [])
    image_catalog_path.write_text(json.dumps(
        {"project_id": args.project_id, "images": existing_images + new_entries},
        indent=2, ensure_ascii=False,
    ) + "\n")

    print(f"\nExtracted {len(new_entries)} images -> {still_dir}")
    print(f"Class breakdown: {class_counts}")
    print(f"Appended to {image_catalog_path}")
    print("All entries needs_human_classification=true - not a final disposition.")


if __name__ == "__main__":
    main()

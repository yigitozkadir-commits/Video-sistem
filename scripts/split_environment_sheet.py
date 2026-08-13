#!/usr/bin/env python3
"""
Part 3 of PRJ-fetih-1453's Higgsfield uploads switched from character
turnaround sheets to environment/scene/asset reference sheets (horse
colour catalogue, the Sultan's tent, the "ships hauled overland" history
scene, a pre-battle army panorama) - landscape 1536x1024 canvases with
their own one-off layouts, not the portrait 1024x1536 CHARACTERS/LAYOUTS
grid split_character_sheet.py expects. Kept as a separate script rather
than forcing these into that script's character-per-sheet model.

Usage:
    python3 scripts/split_environment_sheet.py <source_extract_dir>
Writes crops under projects/PRJ-fetih-1453/assets/reference/ (REF-ENV/
REF-OBJ/REF-PAL, schemas/reference_asset.schema.json) and mood/context
scene crops (schemas/image_catalog.schema.json), appending to the same
state/reference_catalog.jsonl and state/image_catalog.json Part 1/2 wrote.
"""
import hashlib
import json
from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).parent.parent
PROJECT_DIR = REPO_ROOT / "projects" / "PRJ-fetih-1453"
REF_DIR = PROJECT_DIR / "assets" / "reference"
SOURCE_DIR = REF_DIR / "_source"
MOOD_DIR = REF_DIR / "mood"

HORSE_COLORS = ["doru", "al", "kara", "beyaz", "kir", "gri", "alaca", "dilber"]

SHEETS = {
    "horses": {
        "source": "file_0000000042088246b16ad949def231be.png",
        "sheet_title": "At Renkleri ve Detaylı Görünüm Kataloğu",
        "ref_obj": {
            f"{color}_side": (252, 72 + i * 103, 433, 176 + i * 103)
            for i, color in enumerate(HORSE_COLORS)
        },
        "extra_ref_obj": {
            "tack_equipment": (1290, 72, 1536, 176),
            "body_anatomy": (0, 900, 255, 1024),
            "skeleton": (255, 900, 455, 1024),
        },
        "ref_pal": {},
        "mood": {},
    },
    "tent": {
        "source": "file_0000000043948246a6a9332bb295f617.png",
        "sheet_title": "Fatih Sultan Mehmed'in Otağı",
        "ref_env": {
            "interior_hero": (0, 20, 1150, 650),
            "exterior_view": (1180, 55, 1400, 145),
        },
        "ref_obj": {
            "harita_masasi": (410, 720, 620, 850),
            "kitaplar_belgeler": (770, 720, 980, 850),
            "silahlar_zirhlar": (0, 900, 410, 1010),
            "sancaklar_tuglar": (410, 900, 620, 1010),
            "kisisel_esyalar": (620, 900, 1150, 1010),
            "aydinlatma": (1180, 900, 1536, 1010),
            "savas_konseyi": (1180, 760, 1536, 850),
            "symbols": (1180, 635, 1536, 730),
        },
        "ref_pal": {"materials": (1180, 510, 1536, 610)},
        "mood": {},
    },
    "ships": {
        "source": "file_000000004f1082469da467cdc053958d.png",
        "sheet_title": "Gemilerin Karada Yürütülüşü (1453)",
        "ref_env": {"hero_scene": (0, 20, 1536, 780)},
        "ref_obj": {"route_map": (0, 800, 340, 1000)},
        "ref_pal": {},
        "mood": {
            "hazirlik": (600, 800, 745, 975),
            "cekis": (750, 800, 895, 975),
            "ilerleyis": (900, 800, 1015, 975),
            "sur_arkasina_ulasma": (1020, 800, 1135, 975),
            "halice_indiris": (1140, 800, 1245, 975),
        },
    },
    "prebattle": {
        "source": "file_00000000586c8246af7668e9aecd965b.png",
        "sheet_title": "Savaş Öncesi - Düzen ve Hazırlık",
        "ref_env": {"hero_scene": (0, 0, 1536, 855)},
        "ref_obj": {},
        "ref_pal": {},
        "mood": {},
    },
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def crop_and_save(im: Image.Image, box: tuple, out_path: Path) -> dict:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    crop = im.crop(box)
    crop.save(out_path)
    return {
        "path": str(out_path.relative_to(REPO_ROOT)),
        "sha256": sha256_file(out_path),
        "width": crop.width,
        "height": crop.height,
    }


def next_ref_counter(existing_jsonl: Path) -> dict:
    """Resume numbering from what Part 1/2 already wrote, don't collide."""
    counters = {"CHR": 0, "OBJ": 0, "PAL": 0, "ENV": 0}
    if existing_jsonl.exists():
        for line in existing_jsonl.read_text().splitlines():
            row = json.loads(line)
            rid = row.get("reference_id", "")
            for prefix in counters:
                if rid.startswith(f"REF-{prefix}-"):
                    counters[prefix] = max(counters[prefix], int(rid.rsplit("-", 1)[1]))
    return counters


def next_asset_counter(ref_jsonl: Path, img_json: Path) -> int:
    n = 0
    if ref_jsonl.exists():
        for line in ref_jsonl.read_text().splitlines():
            aid = json.loads(line).get("asset_id", "")
            if aid.startswith("AST-IMG-"):
                n = max(n, int(aid.rsplit("-", 1)[1]))
    if img_json.exists():
        for row in json.loads(img_json.read_text())["images"]:
            aid = row.get("asset_id", "")
            if aid.startswith("AST-IMG-"):
                n = max(n, int(aid.rsplit("-", 1)[1]))
    return n


def main(source_extract_dir: Path) -> None:
    ref_jsonl = PROJECT_DIR / "state" / "reference_catalog.jsonl"
    img_json = PROJECT_DIR / "state" / "image_catalog.json"

    ref_counters = next_ref_counter(ref_jsonl)
    asset_n = next_asset_counter(ref_jsonl, img_json)

    def new_asset_id() -> str:
        nonlocal asset_n
        asset_n += 1
        return f"AST-IMG-{asset_n:06d}"

    def new_ref_id(prefix: str) -> str:
        ref_counters[prefix] += 1
        return f"REF-{prefix}-{ref_counters[prefix]:03d}"

    new_ref_entries = []
    new_image_entries = []

    for sheet_key, sheet in SHEETS.items():
        src_path = source_extract_dir / sheet["source"]
        if not src_path.exists():
            print(f"SKIP {sheet_key}: source not found ({src_path})")
            continue
        im = Image.open(src_path).convert("RGB")
        archived = SOURCE_DIR / f"ENV-{sheet_key}_{sheet['source']}"
        if not archived.exists():
            im.save(archived)
        sheet_asset_id = new_asset_id()

        counts = {"REF-ENV": 0, "REF-OBJ": 0, "REF-PAL": 0, "mood": 0}

        for panel, box in {**sheet.get("ref_env", {})}.items():
            ref_id = new_ref_id("ENV")
            out = REF_DIR / f"{ref_id}_{sheet_key}_{panel}.png"
            info = crop_and_save(im, box, out)
            new_ref_entries.append({
                "reference_id": ref_id, "asset_id": new_asset_id(), "class": "environment",
                "path": info["path"], "sha256": info["sha256"], "immutable": True,
                "derived_from": sheet_asset_id,
                "notes": f"{sheet['sheet_title']} - panel: {panel}",
            })
            counts["REF-ENV"] += 1

        for panel, box in {**sheet.get("ref_obj", {}), **sheet.get("extra_ref_obj", {})}.items():
            ref_id = new_ref_id("OBJ")
            out = REF_DIR / f"{ref_id}_{sheet_key}_{panel}.png"
            info = crop_and_save(im, box, out)
            new_ref_entries.append({
                "reference_id": ref_id, "asset_id": new_asset_id(), "class": "object",
                "path": info["path"], "sha256": info["sha256"], "immutable": True,
                "derived_from": sheet_asset_id,
                "notes": f"{sheet['sheet_title']} - panel: {panel}",
            })
            counts["REF-OBJ"] += 1

        for panel, box in sheet.get("ref_pal", {}).items():
            ref_id = new_ref_id("PAL")
            out = REF_DIR / f"{ref_id}_{sheet_key}_{panel}.png"
            info = crop_and_save(im, box, out)
            new_ref_entries.append({
                "reference_id": ref_id, "asset_id": new_asset_id(), "class": "palette",
                "path": info["path"], "sha256": info["sha256"], "immutable": True,
                "derived_from": sheet_asset_id,
                "notes": f"{sheet['sheet_title']} - panel: {panel}",
            })
            counts["REF-PAL"] += 1

        for panel, box in sheet.get("mood", {}).items():
            out = MOOD_DIR / f"ENV-{sheet_key}_{panel}.png"
            info = crop_and_save(im, box, out)
            new_image_entries.append({
                "asset_id": new_asset_id(),
                "page": 0,
                "sha256": info["sha256"],
                "class": "illustration",
                "caption_nearby": f"{sheet['sheet_title']} - {panel.replace('_', ' ')}",
                "scores": {
                    "narrative_relevance": 75, "visual_quality": 85,
                    "resolution_adequacy": 60, "reuse_potential": 55, "reference_value": 80,
                },
                "disposition": "REFERENCE_ONLY",
                "rationale": (
                    f"Higgsfield çevre/sahne referans sayfasından ({sheet['sheet_title']}) "
                    f"mekanik olarak kırpıldı; henüz insan gözden geçirmesi yapılmadı."
                ),
            })
            counts["mood"] += 1

        print(f"{sheet_key}: {counts['REF-ENV']} REF-ENV, {counts['REF-OBJ']} REF-OBJ, "
              f"{counts['REF-PAL']} REF-PAL, {counts['mood']} mood")

    with open(ref_jsonl, "a") as f:
        for entry in new_ref_entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    existing_images = []
    if img_json.exists():
        existing_images = json.loads(img_json.read_text())["images"]
    img_json.write_text(json.dumps(
        {"project_id": "PRJ-fetih-1453", "images": existing_images + new_image_entries},
        indent=2, ensure_ascii=False,
    ) + "\n")

    print(f"\nAppended {len(new_ref_entries)} reference_asset entries -> {ref_jsonl}")
    print(f"Appended {len(new_image_entries)} image_catalog entries -> {img_json}")


if __name__ == "__main__":
    import sys
    source_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if source_dir is None:
        print("Usage: split_environment_sheet.py <source_extract_dir>")
        sys.exit(1)
    main(source_dir)

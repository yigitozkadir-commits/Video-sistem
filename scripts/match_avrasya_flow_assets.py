#!/usr/bin/env python3
"""
Matches Flow-delivered asset files (auto-named by Flow from a salient phrase
in the PROMPT text, e.g. "Feather_grass_seed_heads_202608072013.jpeg") back
to their SC-0XX scene/slot, using word-overlap scoring against the exact
PROMPT text in prompts_used/FLOW_PROMPTS_chunk_{A,B,C}_v1.txt.

This is the standing pattern for every future Kaggle-delivered Flow batch
(CLAUDE.md decision, 2026-08-07): user uploads a dataset instead of sending
files one by one, this script matches names to slots, low-confidence matches
are never auto-accepted - they go to a review list instead of being guessed.

Usage:
    python3 scripts/match_avrasya_flow_assets.py <downloaded_dir>
"""
import json
import re
import sys
import shutil
import time
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
PROJECT_DIR = REPO_ROOT / "projects" / "PRJ-avrasya-bozkir-kusagi"
PROMPT_FILES = [
    REPO_ROOT / "projects/PRJ-avrasya-bozkir-kusagi/prompts_used/FLOW_PROMPTS_chunk_A_v1.txt",
    REPO_ROOT / "projects/PRJ-avrasya-bozkir-kusagi/prompts_used/FLOW_PROMPTS_chunk_B_v1.txt",
    REPO_ROOT / "projects/PRJ-avrasya-bozkir-kusagi/prompts_used/FLOW_PROMPTS_chunk_C_v1.txt",
]
STOPWORDS = {
    "a", "an", "the", "of", "in", "on", "with", "and", "to", "at", "into",
    "across", "from", "over", "under", "-", "no", "is", "its", "each",
}

SLOT_RE = re.compile(r"^--- (SC-\d+)_(img\d+|video) \(([^)]*)\) ---$")


def normalize(text: str) -> set[str]:
    words = re.findall(r"[a-z]+", text.lower())
    return {w for w in words if w not in STOPWORDS and len(w) > 2}


def load_slots() -> list[dict]:
    slots = []
    for pf in PROMPT_FILES:
        text = pf.read_text()
        blocks = text.split("--- ")
        for block in blocks[1:]:
            block = "--- " + block
            header_match = SLOT_RE.match(block.splitlines()[0])
            if not header_match:
                continue
            sid, slot, desc_tr = header_match.groups()
            prompt_match = re.search(r"PROMPT:\s*(.+?)\nFLOW SETTINGS:", block, re.DOTALL)
            prompt_text = prompt_match.group(1).replace("\n", " ") if prompt_match else ""
            slots.append({
                "scene_id": sid,
                "slot": slot,
                "desc_tr": desc_tr,
                "prompt_words": normalize(prompt_text),
                "is_video": slot == "video",
            })
    return slots


def score(file_words: set[str], slot_words: set[str]) -> float:
    if not file_words or not slot_words:
        return 0.0
    overlap = len(file_words & slot_words)
    return overlap / len(file_words)  # fraction of the filename's words explained by this prompt


MIN_SCORE = 0.5


def main():
    if len(sys.argv) not in (2, 3):
        print("Usage: python3 scripts/match_avrasya_flow_assets.py <downloaded_dir> [restrict_slots_file]")
        print("  restrict_slots_file: one SC-0XX_slot per line - narrows the matching")
        print("  universe to only these slots, avoiding cross-contamination from the")
        print("  other ~50 unrelated slots' shared vocabulary (soil/sample/texture etc).")
        print("  Use this whenever the batch is a closed-set regeneration of known slots.")
        sys.exit(1)
    src_dir = Path(sys.argv[1])
    slots = load_slots()
    slot_by_key = {(s["scene_id"], s["slot"]): s for s in slots}

    if len(sys.argv) == 3:
        restrict = {line.strip() for line in Path(sys.argv[2]).read_text().splitlines() if line.strip()}
        slots = [s for s in slots if f"{s['scene_id']}_{s['slot']}" in restrict]
        slot_by_key = {(s["scene_id"], s["slot"]): s for s in slots}
        missing_from_prompts = restrict - {f"{s['scene_id']}_{s['slot']}" for s in slots}
        if missing_from_prompts:
            print(f"WARNING: {len(missing_from_prompts)} restrict-list slot(s) not found in prompt files: {sorted(missing_from_prompts)}")
        print(f"Restricted matching universe to {len(slots)} slot(s) from {sys.argv[2]}")

    files = sorted([f for f in src_dir.iterdir() if f.is_file()])
    file_words_map = {}
    for f in files:
        stem = re.sub(r"_\d{12,}(_\d+)?$", "", f.stem)
        file_words_map[f] = normalize(stem.replace("_", " ").replace("…", ""))

    # Build every (score, file, slot_key) pair above threshold, matching type (image/video)
    pairs = []
    for f in files:
        is_video = f.suffix.lower() in (".mp4", ".mov", ".webm")
        fw = file_words_map[f]
        for s in slots:
            if s["is_video"] != is_video:
                continue
            sc = score(fw, s["prompt_words"])
            if sc >= MIN_SCORE:
                pairs.append((sc, f, (s["scene_id"], s["slot"])))
    pairs.sort(key=lambda x: -x[0])

    primary = {}   # slot_key -> file
    alt = {}       # slot_key -> [files]
    assigned_files = set()

    # Pass 1: greedy best-score-first, fill each slot's primary once
    for sc, f, key in pairs:
        if f in assigned_files:
            continue
        if key not in primary:
            primary[key] = (f, sc)
            assigned_files.add(f)

    # Pass 2: leftover files go to the best-scoring slot as an alt (even if already primaried)
    for sc, f, key in pairs:
        if f in assigned_files:
            continue
        alt.setdefault(key, []).append((f, sc))
        assigned_files.add(f)

    review = [f for f in files if f not in assigned_files]

    print(f"Primary matches: {len(primary)}")
    print(f"Alt (extra candidates for an already-filled slot): {sum(len(v) for v in alt.values())}")
    print(f"True review (no candidate scored >= {MIN_SCORE}): {len(review)}")
    print()
    if review:
        print("=== TRUE REVIEW NEEDED (no confident match at all) ===")
        for f in review:
            print(f"  {f.name}")

    out = {
        "primary": {f"{k[0]}_{k[1]}": {"file": v[0].name, "score": round(v[1], 2)} for k, v in primary.items()},
        "alt": {f"{k[0]}_{k[1]}": [{"file": f.name, "score": round(s, 2)} for f, s in v] for k, v in alt.items()},
        "review": [f.name for f in review],
    }
    out_path = PROJECT_DIR / "state" / "flow_asset_match_report.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"\nFull report: {out_path}")

    all_slot_keys = {(s["scene_id"], s["slot"]) for s in slots}
    missing = sorted(all_slot_keys - set(primary.keys()))
    print(f"\nSlots with NO match at all ({len(missing)}) - still need Flow generation:")
    for sid, slot in missing:
        print(f"  {sid}_{slot}: {slot_by_key[(sid, slot)]['desc_tr']}")

    # Copy primaries into place - never overwrite blind: archive any existing
    # destination file first (CLAUDE.md "never delete, archive instead").
    archive_dir = PROJECT_DIR / "assets" / "_archived"
    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    ext_map_still = {".jpeg": ".jpg", ".jpg": ".jpg", ".png": ".png"}
    archived = 0
    for (sid, slot), (f, sc) in primary.items():
        if slot == "video":
            dest = PROJECT_DIR / "assets" / "video" / f"{sid}_video.mp4"
        else:
            n = slot.replace("img", "")
            ext = ext_map_still.get(f.suffix.lower(), f.suffix.lower())
            dest = PROJECT_DIR / "assets" / "still" / f"{sid}_img{n}{ext}"
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            archive_dir.mkdir(parents=True, exist_ok=True)
            archive_dest = archive_dir / f"{sid}_{slot}_{ts}_prev{dest.suffix}"
            shutil.copy2(dest, archive_dest)
            archived += 1
        shutil.copy2(f, dest)
    print(f"\nCopied {len(primary)} primary files into projects/PRJ-avrasya-bozkir-kusagi/assets/ "
          f"({archived} pre-existing file(s) archived to assets/_archived/ before being replaced)")


if __name__ == "__main__":
    main()

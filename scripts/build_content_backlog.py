#!/usr/bin/env python3
"""
Parses the studio's bulk content-idea source (input/ilk_1000_icerik.txt,
a `pandoc -t plain` extraction of the uploaded .docx) into
projects/_content_backlog/state/content_backlog.json - see the 2026-08-09
content-roadmap plan (1050 items -> short_new / short_repurpose / long /
epic tiers) for the full rationale.

Source structure: the document has an EARLIER unnumbered draft
categorization (A-F KATEGORİSİ / A-G KATMANI, before the authoritative
numbered list) that the document's own text says was superseded ("bu
yüzden 6 aylık planı yeniden sıralamak lazım"). Only the numbered 1-1050
list (starting at "A KATMANI — MERAK VE HAFIZA (1-30)") is parsed - the
draft section before it is intentionally skipped.

Section -> tier mapping is hardcoded below, matching the content-roadmap
plan's classification table exactly. If the source document changes
(more items, renamed sections), update SECTION_TIER_MAP accordingly - do
not guess a heuristic classifier, this is a human strategic call recorded
once and reused, not a thing to re-derive per run (CLAUDE.md law #1,
contract over prose: the table below IS the contract).

Usage:
    python3 scripts/build_content_backlog.py
"""
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
SOURCE_TXT = REPO_ROOT / "projects" / "_content_backlog" / "input" / "ilk_1000_icerik.txt"
OUT_PATH = REPO_ROOT / "projects" / "_content_backlog" / "state" / "content_backlog.json"

# Anchor line: everything before this in the source is the superseded
# early draft (A-F KATEGORİSİ / A-G KATMANI) and is skipped.
START_ANCHOR = "A KATMANI — MERAK VE HAFIZA (1-30)"

RYSKULOV_MASTER = "repurpose:mehmetkync16/ai-audiobook-studio-videos:ryskulov_mektubu_master.mp4"

# section header (as it appears, stripped of any "(n-m)"/"SERİ n-m" suffix)
# -> (tier, source, consolidation_group_prefix or None)
SECTION_TIER_MAP = {
    "A KATMANI — MERAK VE HAFIZA": ("short_new", "new", None),
    "BÖLÜM 1 — BOZKIRIN DOĞUŞU": ("short_new", "new", None),
    "KURGANLAR": ("short_new", "new", None),  # audited for repurpose overlap separately, task #59
    "KÜR-ARAZ VE ERKEN DÜNYA": ("short_new", "new", None),
    "MİTOLOJİ": ("short_new", "new", None),
    "ESKİ HALKLAR": ("short_new", "new", None),
    "BÜYÜK DEVLETLER": ("long", "new", "buyuk-devletler"),
    "DAMGALAR SERİSİ": ("short_new", "new", None),
    "ATASÖZLERİ SERİSİ": ("short_new", "new", None),
    "İSİMLER SERİSİ": ("short_new", "new", None),
    "ORTAK SEMBOLLER": ("short_new", "new", None),
    "TÜRK DÜNYASI HALKLARI": ("short_new", "new", None),
    "YAŞAYAN MİRAS": ("short_new", "new", None),
    "HAFIZANIN SINAVI": ("short_new", "new", None),
    "KÜLTÜREL ŞOKLAR": ("short_new", "new", None),
    "BOZKIR FELSEFESİ": ("long", "new", "bozkir-felsefesi"),
    "OĞUZ BOYLARI": ("short_new", "new", None),
    "DEDE KORKUT EVRENİ": ("epic", "new", "dede-korkut"),
    "MANAS EVRENİ": ("epic", "new", "manas"),
    "MÜZİK VE SESLER": ("short_new", "new", None),
    "AŞARŞILIK EVRENİ": ("short_repurpose", RYSKULOV_MASTER, None),
    "RYSKULOV DOSYASI": ("short_repurpose", RYSKULOV_MASTER, None),
    "TÜRKİSTAN AYDINLARI": ("long", "new", "turkistan-aydinlari"),
}

# Header lines in the txt carry a "(n-m)" or stand alone right after a
# "SERİ n-m" marker line - strip any trailing " (...)" before lookup.
_HEADER_SUFFIX_RE = re.compile(r"\s*\([0-9]+-[0-9]+\)\s*$")
_ITEM_RE = re.compile(r"^(\d{1,4})\.\s+(.*\S)\s*$")


def main():
    if not SOURCE_TXT.exists():
        print(f"ERROR: {SOURCE_TXT} not found", file=sys.stderr)
        sys.exit(1)

    lines = SOURCE_TXT.read_text(encoding="utf-8").splitlines()
    start_idx = next((i for i, l in enumerate(lines) if l.strip() == START_ANCHOR), None)
    if start_idx is None:
        print(f"ERROR: anchor line {START_ANCHOR!r} not found - source format changed?", file=sys.stderr)
        sys.exit(1)

    current_section = None
    items = []
    seen_numbers = set()

    for line in lines[start_idx:]:
        stripped = line.strip()
        if not stripped:
            continue
        header_candidate = _HEADER_SUFFIX_RE.sub("", stripped).strip()
        if header_candidate in SECTION_TIER_MAP or header_candidate == "A KATMANI — MERAK VE HAFIZA":
            current_section = header_candidate
            continue
        m = _ITEM_RE.match(stripped)
        if not m:
            continue
        number = int(m.group(1))
        title = m.group(2)
        if number in seen_numbers:
            continue  # defensive: a stray "N." elsewhere in prose should not double-count
        if current_section is None:
            continue
        tier, source, group_prefix = SECTION_TIER_MAP[current_section]
        group = f"{group_prefix}" if group_prefix else None
        items.append({
            "backlog_id": f"CB-{number:04d}",
            "source_number": number,
            "section": current_section,
            "title": title,
            "tier": tier,
            "source": source,
            "consolidation_group": group,
            "status": "not_started",
            "project_ref": None,
        })
        seen_numbers.add(number)

    items.sort(key=lambda i: i["source_number"])

    tier_counts = {}
    for it in items:
        tier_counts[it["tier"]] = tier_counts.get(it["tier"], 0) + 1

    missing = sorted(set(range(1, 1051)) - seen_numbers)
    out = {
        "generated_from": "projects/_content_backlog/input/ilk_1000_icerik.txt",
        "source_docx_sha256_ref": "projects/_content_backlog/input/ilk_1000_icerik.docx",
        "total_items": len(items),
        "tier_counts": tier_counts,
        "known_source_gaps": {
            "missing_numbers": missing,
            "note": "The source document's own numbering jumps from 500 straight to 551 ('SERİ 551-600' follows item 500 directly) - items 501-550 were never written in the source, not a parsing bug. Confirmed by direct inspection of the source text around that boundary. The document's closing line ('liste 1050 içerik başlığını geçti') describes the highest NUMBER used, not the true item count (1000, not 1050).",
        },
        "items": items,
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Parsed {len(items)} items (source document's own numbering runs 1-1050 but skips 501-550, see known_source_gaps).")
    print("Tier counts:", tier_counts)
    if missing:
        print(f"WARNING: {len(missing)} item numbers missing from parse: {missing[:20]}{'...' if len(missing) > 20 else ''}")
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()

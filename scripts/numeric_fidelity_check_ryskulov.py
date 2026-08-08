#!/usr/bin/env python3
"""
Numeric-fidelity check for PRJ-ryskulov-mektubu (project.json decisions_log,
2026-08-07 - user-requested extra verification step after choosing Flow-heavy
production over Remotion-native charts: exact figures live only in spoken
narration, so the narration itself is the single point of numeric truth and
must be checked against the source docx, not just scanned for bare digits).

This is a "golden fact checklist", not a generic Turkish-number-word parser:
each entry is (scene_id, expected_spelled_substring, source_docx_figure) drawn
directly from input/RYSKULOV_ARASTIRMA_RAPORU.docx while writing
scaffold_ryskulov_project.py's SCENES list. Checks that the exact spelled
Turkish phrase for each figure is present verbatim in that scene's committed
source_text - catches typos/wrong-number mistakes made while spelling numbers
out by hand, which the "no bare digits" regex scan (scaffold script's own
assert) cannot catch since it only looks for the ABSENCE of digits, not the
CORRECTNESS of the words that replaced them.

Usage:
    python3 scripts/numeric_fidelity_check_ryskulov.py
"""
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
PROJECT_DIR = REPO_ROOT / "projects" / "PRJ-ryskulov-mektubu"

# (scene_id, expected substring, docx figure this represents)
GOLDEN_FACTS = [
    ("SC-002", "dokuz Mart bin dokuz yüz otuz üç", "9 Mart 1933 (mektup tarihi)"),
    ("SC-003", "bin dokuz yüz otuz ile bin dokuz yüz otuz üç", "1930-1933 (Aşarşılık dönemi)"),
    ("SC-005", "bin sekiz yüz doksan dört", "1894 (Ryskulov'un doğum yılı)"),
    ("SC-006", "on bir yıl", "11 yıl (RSFSR Başkan Yardımcılığı süresi)"),
    ("SC-009", "bin dokuz yüz otuz yedi", "1937 (tutuklanma yılı)"),
    ("SC-009", "bin dokuz yüz otuz sekiz", "1938 (idam yılı)"),
    ("SC-011", "bin dokuz yüz otuz bir", "1931 (Goloshchekin'in açıklaması)"),
    ("SC-012", "Temmuz bin dokuz yüz otuz iki", "Temmuz 1932 (Beşlerin Mektubu)"),
    ("SC-013", "5 Temmuz".replace("5", "beş"), "5 Temmuz 1932 (toplantı tarihi)"),
    ("SC-015", "yirmi dokuz Eylül bin dokuz yüz otuz iki", "29 Eylül 1932 (ilk not)"),
    ("SC-016", "dokuz Mart bin dokuz yüz otuz üç", "9 Mart 1933 (asıl mektup)"),
    ("SC-017", "dokuz Mart bin dokuz yüz otuz üç", "9 Mart 1933 (mektup tarihi, alıntı altyazısı)"),
    ("SC-018", "yüzde yirmi sekiz", "%28 (Aktubinsk kaybı)"),
    ("SC-018", "yüzde seksen ile seksen beş arası", "%80-85 (Kızılorda kaybı)"),
    ("SC-018", "yüzde seksen kayıp", "%80 (Balkaş kaybı)"),
    ("SC-019", "yüzde on beş ile yirmisi", "%15-20 (Kızılorda'da yerinde kalan nüfus)"),
    ("SC-021", "bir milyondan fazla", "1 milyon+ (cumhuriyet dışına kaçış)"),
    ("SC-021", "altı yüz on altı bin", "616.000 (geri dönmeyenler)"),
    ("SC-022", "dört buçuk milyon", "4,5 milyon (1 Ocak 1933 hayvan varlığı)"),
    ("SC-022", "kırk buçuk milyon", "40,5 milyon (kolektifleştirme öncesi hayvan varlığı)"),
    ("SC-023", "üç yüz on üç bin", "313.000 (1930 ölü sayısı)"),
    ("SC-023", "yedi yüz elli beş bin", "755.000 (1931 ölü sayısı)"),
    ("SC-023", "yedi yüz altmış dokuz bin", "769.000 (1932 ölü sayısı)"),
    ("SC-023", "iki milyon yüz bin", "2,1 milyon (e-history.kz toplamı)"),
    ("SC-023", "bir buçuk milyon", "1,5 milyon (Cameron/Kindler/Ohayon tahmini)"),
    ("SC-025", "altı yüz altmış beş bin", "665.000 (iade edilen kişi sayısı)"),
    ("SC-026", "Ocak bin dokuz yüz otuz üç", "Ocak 1933 (Goloshchekin'in görevden alınması)"),
    ("SC-027", "en az üç kez", "en az üç kez (Stalin'in bilgilendirilmesi)"),
    ("SC-028", "iki yüzden az ilçenin otuz ikisi", "<200 ilçeden 32'si (kara liste)"),
    ("SC-034", "bin dokuz yüz seksenlerin sonuna", "1980'lerin sonu (glasnost)"),
    ("SC-035", "iki bin üçte", "2003 (Werth'in çalışması)"),
    ("SC-036", "bin dokuz yüz doksan yedide", "1997 (külliyatın yayımlanması)"),
    ("SC-040", "bin dokuz yüz doksan bir sonrası", "1991 sonrası (Kazakistan'da tanınma)"),
    ("SC-042", "bin dokuz yüz otuz yedide", "1937 (tutuklanma)"),
    ("SC-042", "bin dokuz yüz otuz sekizde kurşuna dizildi", "1938 (idam)"),
    ("SC-043", "bin dokuz yüz elli altıda", "1956 (rehabilitasyon)"),
    ("SC-045", "bin dokuz yüz otuz sekizde kurşuna dizildi", "1938 (idam, kapanış alıntısı)"),
    ("SC-045", "bin dokuz yüz doksan yediye kadar", "1997'ye kadar (arşivde kalış)"),
]


def tr_fold(s: str) -> str:
    # Python's str.lower()/casefold() mishandle Turkish İ (-> "i" + combining
    # dot, not plain "i"), which breaks sentence-initial-capital comparisons
    # like "İki yüzden..." vs an expected "iki yüzden...". Map both Turkish
    # capital forms to plain lowercase "i" before folding the rest normally -
    # good enough for this checklist's ASCII-heavy number-word phrases.
    return s.replace("İ", "i").replace("I", "i").lower()


def main() -> None:
    scenes = {}
    for p in sorted(PROJECT_DIR.glob("scenes/SC-*.json")):
        d = json.loads(p.read_text())
        scenes[d["scene_id"]] = d["source_text"]

    findings = []
    for sid, expected, fact in GOLDEN_FACTS:
        text = scenes.get(sid)
        if text is None:
            findings.append({"scene_id": sid, "fact": fact, "issue": "scene_not_found"})
            continue
        if tr_fold(expected) not in tr_fold(text):
            findings.append({
                "scene_id": sid, "fact": fact, "issue": "expected_phrase_not_found",
                "expected": expected, "actual_text": text,
            })

    out = {
        "checked_at": "generator-run",
        "total_facts_checked": len(GOLDEN_FACTS),
        "findings": findings,
        "status": "clean" if not findings else "REVIEW_NEEDED",
    }
    out_path = PROJECT_DIR / "state" / "numeric_fidelity_check.json"
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")

    print(f"Checked {len(GOLDEN_FACTS)} golden facts across {len(scenes)} scenes.")
    if findings:
        print(f"\n{len(findings)} FINDING(S) - review before narration generation:")
        for f in findings:
            print(f"  {f['scene_id']}: {f['fact']} - {f['issue']}")
        sys.exit(1)
    print("Clean - every golden fact's spelled figure found verbatim in its scene's source_text.")


if __name__ == "__main__":
    main()

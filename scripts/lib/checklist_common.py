"""
Shared building blocks for the project-specific pre_render_checklist_*.py
scripts. Extracted 2026-08-08 after confirming these exact pieces were
byte-identical duplicates across pre_render_checklist_avrasya.py and
pre_render_checklist_ryskulov.py (and the constants also matched
pre_render_checklist.py's, the original Başkurtlar script) - not a
speculative abstraction, a real duplication removal.

Each checklist script stays project-specific (different visual models,
different extra checks like citation refs or forbidden-content scans) -
this module only holds the parts that were doing the exact same thing
under different names.
"""
import re
import subprocess
from pathlib import Path

# Calibrated against PRJ-baskurtlar-arastirma's real faster-whisper
# evidence (see pre_render_checklist.py's docstring): 4-digit years spelled
# out (~5 words) transcribed cleanly every time; the one confirmed garble
# (SC-001's population figure) was ~11 words. Threshold sits between the
# two so ordinary years don't trigger constant false alarms.
LONG_NUMBER_WORD_THRESHOLD = 8

NUMBER_WORDS = {
    "bir", "iki", "üç", "dört", "beş", "altı", "yedi", "sekiz", "dokuz",
    "on", "yirmi", "otuz", "kırk", "elli", "altmış", "yetmiş", "seksen",
    "doksan", "yüz", "bin", "milyon", "milyar",
}


def probe_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True,
    ).stdout.strip()
    return float(out) if out else 0.0


def long_compound_number_findings(scenes: list[dict]) -> list[str]:
    """scenes: list of scene dicts (already-loaded scenes/SC-*.json), each
    needs 'scene_id' and 'source_text'. Flags any run of >= threshold
    consecutive Turkish number-words in a scene's narration text as
    worth a faster-whisper listen-check before render (ElevenLabs has
    garbled runs like this before - see NAR-SC-001 history)."""
    findings = []
    for s in scenes:
        text = s.get("source_text", "")
        words = re.findall(r"[\wşŞğĞıİöÖüÜçÇ]+", text.lower())
        run_start, run_len = None, 0
        for i, w in enumerate(words):
            if w in NUMBER_WORDS:
                if run_start is None:
                    run_start = i
                run_len += 1
            else:
                if run_len >= LONG_NUMBER_WORD_THRESHOLD:
                    phrase = " ".join(words[run_start:i])
                    findings.append(f"{s['scene_id']}: long compound number run ({run_len} words) - \"{phrase}\"")
                run_start, run_len = None, 0
        if run_len >= LONG_NUMBER_WORD_THRESHOLD:
            phrase = " ".join(words[run_start:])
            findings.append(f"{s['scene_id']}: long compound number run ({run_len} words) - \"{phrase}\"")
    return findings

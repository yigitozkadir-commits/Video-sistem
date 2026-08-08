#!/usr/bin/env python3
"""
Pre-render checklist for PRJ-ninniler-atlasi (CLAUDE.md section 10: "A
future project with a different Remotion architecture needs an equivalent
script - write one before that project's first full render, not after the
first complaint"). No full/final render of any of the 22 lullaby videos has
happened yet (all 22 are still PLACEHOLDER-timed - see lullabies.ts header,
real timing pending music), so this script closes the gap before that
happens, not after.

This project's architecture differs from the video-hero-scene projects
pre_render_checklist.py/_avrasya.py/_ryskulov.py were built for: one
LULLABIES[] entry per nation, each with a single very-long scene (2700
frames / 20 still slots, no video-type slots at all) rather than many
short scenes mixing video+still. The long-compound-number and
video-loop-ratio checks those scripts run don't apply here (no narration
yet at all - silent placeholder video; no video-type slots to loop). What
DOES apply, and is new to this project, is scripts/lib/slideshow_risk.py's
style-relative slideshow-risk scoring (item 1.3 - see
HANDOFF_OPENMONTAGE_PROPOSAL.md): with 20 still slots per lullaby reusing
a shared image pool across many of the 22 nations (decisions/0002), the
real risk here is slot pacing drifting from the template's declared pace
and/or the same image landing in back-to-back slots - exactly what that
module checks for.

Usage:
    python3 scripts/pre_render_checklist_ninniler.py
Exit code 0 = clean, 1 = findings need review before rendering (does not
block, just refuses to claim "all clear" - CLAUDE.md law #4).
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from lib.slideshow_risk import slideshow_risk_findings  # noqa: E402

PROJECT_DIR = REPO_ROOT / "projects" / "PRJ-ninniler-atlasi"
REMOTION_DIR = REPO_ROOT / "remotion_ninniler_atlasi"
PROJECT_JSON = PROJECT_DIR / "project.json"
LULLABIES_TS = REMOTION_DIR / "src" / "lullabies.ts"
COMPOSITION_TSX = REMOTION_DIR / "src" / "compositions" / "StudioComposition.tsx"


def main():
    all_findings = []
    if not LULLABIES_TS.exists():
        print(f"WARN: {LULLABIES_TS} not found, skipping slideshow-risk check", file=sys.stderr)
    else:
        all_findings += slideshow_risk_findings(PROJECT_JSON, LULLABIES_TS, COMPOSITION_TSX)

    if not all_findings:
        print("Pre-render checklist (ninniler): clean. 0 findings.")
        sys.exit(0)

    print(f"Pre-render checklist (ninniler): {len(all_findings)} finding(s) - review before full render:\n")
    for f in all_findings:
        print(f"  - {f}")
    sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Populates schemas/run_manifest.schema.json: one record per production run,
carrying what CLAUDE.md law #5 asks for ("record model, version, seed,
prompt version") so law #8's acceptance test - "studio why <artifact> must
be answerable from the logs alone" - has an actual file to point at instead
of the answer being "re-derive it from memory."

global_seed: this pipeline has no stochastic generation step to seed.
ElevenLabs narration (text, voice, model) are fixed inputs with no seed
parameter in the API, and the atlas project deliberately uses the PDF's
own images rather than generating any (see project history: "0 AI-generated
video"). A fixed sentinel of 0 is recorded rather than omitting the
required field or implying randomness that isn't there.

Usage:
    python3 scripts/write_run_manifest.py --backfill
        Writes one run_manifest entry per distinct run_id already present
        in each project's state/render_manifest.jsonl - reusing that run_id
        (not inventing a new one) so the two logs correlate by run_id.
"""
import glob
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

BIBLE_VERSION = json.loads((REPO_ROOT / "studio.config.json").read_text())["bible_version"]

MODELS = [
    {"role": "narration", "provider": "elevenlabs", "model": "eleven_multilingual_v2", "version": "v2"},
    {"role": "render", "provider": "remotion", "model": "remotion-render", "version": "4.0.506"},
]


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def backfill_project(project_id: str) -> int:
    state_dir = REPO_ROOT / "projects" / project_id / "state"
    render_rows = load_jsonl(state_dir / "render_manifest.jsonl")
    if not render_rows:
        return 0

    by_run_id: dict[str, list[dict]] = {}
    for row in render_rows:
        by_run_id.setdefault(row["run_id"], []).append(row)

    existing = load_jsonl(state_dir / "run_manifest.jsonl")
    already_have = {r["run_id"] for r in existing}

    written = 0
    with open(state_dir / "run_manifest.jsonl", "a") as f:
        for run_id, rows in sorted(by_run_id.items()):
            if run_id in already_have:
                continue
            all_success = all(r["result"] == "success" for r in rows)
            manifest = {
                "run_id": run_id,
                "project_id": project_id,
                "started_at": min(r["started_at"] for r in rows),
                "finished_at": max(r["finished_at"] for r in rows),
                "bible_version": BIBLE_VERSION,
                "models": MODELS,
                "global_seed": 0,
                "prompt_versions": [],
                "replay_broken": False,
                "result": "complete" if all_success else "aborted",
            }
            f.write(json.dumps(manifest, ensure_ascii=False) + "\n")
            written += 1
    return written


def main() -> None:
    if "--backfill" not in sys.argv:
        print(__doc__)
        sys.exit(1)
    for p in sorted(glob.glob(str(REPO_ROOT / "projects" / "PRJ-*"))):
        project_id = Path(p).name
        n = backfill_project(project_id)
        if n:
            print(f"{project_id}: {n} run_manifest entr{'y' if n == 1 else 'ies'} written")


if __name__ == "__main__":
    main()

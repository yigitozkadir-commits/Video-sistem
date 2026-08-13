# Gök Umay — AI Audiobook Studio OS

A provider-agnostic production system that turns a source document (book,
research report, archival letter) into a cinematic narrated video, with a
recorded reason for every creative choice and enough provenance to answer
"why does this artifact look/sound like this" from the logs alone.

This package is the **reusable system** distilled from a working
production repo that has delivered 3 full videos and has 2 more in
production. It ships the engine, not the content: no finished videos, no
project-specific assets, no API keys.

## Quick start

```bash
unzip gokumay_studio_os.zip -d my-studio
cd my-studio
bash scripts/install.sh          # creates directories, checks tools, pip installs
cp .env.example .env             # fill in real API keys (never commit this file)
python3 scripts/validate.py      # should report 0 errors
```

Then open the repo root in Claude Code and let it read `CLAUDE.md` first —
that file is the entry point and tells it exactly what to load next for
any given task (see `CLAUDE.md` section 1, "bounded context").

## What's in here

| Path | Contents |
|------|----------|
| `CLAUDE.md` | Entry point / operating instructions for Claude Code — read this first |
| `bible/` | 22 modules + architecture review — the law of the system |
| `schemas/` | 35 JSON Schemas — every inter-agent contract |
| `templates/` | 18 production presets (channel formats, content-rule sets, visual/audio direction) |
| `style/` | 14 visual style profiles (palette, forbidden content, disclosure rules) |
| `prompts/` | Versioned prompt objects (`PV-*`) + combinatorial axes for building new ones |
| `reports/` | Channel-format-intelligence profiles (`CFP-*`) — distilled analysis of reference channels' craft, used to build new templates |
| `scripts/` | All production tooling — scaffolding, narration, scene-data generation, checklists, Kaggle delivery, validation. See below. |
| `brand/` | Studio identity: voice/palette presets (`gokumay_studio.json`) + the signature outro clip |
| `remotion_template/` | Canonical Remotion composition skeleton — copy this per new project (`scripts/remotion_setup.sh`) |
| `projects/_scaffold/` | Empty per-project directory structure to copy for a new project |
| `projects/project.example.json` | Annotated example of a project's root config |
| `.github/workflows/render.yml` | Optional CI: manual-trigger matrix render on GitHub Actions runners |
| `requirements.txt` | Python dependencies |

## The eight laws (from CLAUDE.md — read the full file for context)

1. Contract over prose — every message validates against `schemas/`
2. Single Writer — one agent/script owns each path
3. Narration is the clock — visuals bend to audio, never the reverse
4. No silent degradation — every compromise emits a finding
5. Deterministic replay — record model, version, seed, prompt version
6. Cost is a constraint — budget exhaustion halts production
7. Human gates are explicit objects with scope and expiry
8. Fail loud, resume cheap — stop the smallest unit, resume from checkpoint

## Starting a new project

```bash
mkdir -p projects/PRJ-myproject
cp projects/_scaffold/* -r projects/PRJ-myproject/   # or write project.json from scratch
cp projects/project.example.json projects/PRJ-myproject/project.json
# edit: project_id, title, source.file + sha256, rights.source_basis,
#       template_ref, language, budget

scripts/remotion_setup.sh PRJ-myproject   # copies remotion_template/ -> remotion_myproject/
cd remotion_myproject && npm install
```

`rights.source_basis` must never stay `unknown` — the system halts on it by
design (see `bible/Module_12_AI_Quality_Assurance_Bible.md` §11).

From there, the established pattern (proven across 5 real projects) is:
write a `scripts/scaffold_<project>_project.py` (adapt
`scripts/scaffold_ryskulov_project.py` or `scaffold_baskurtlar_project.py`)
that emits `scenes/SC-*.json` + `prompts_used/<shot_id>/{image,video}.json`
from your source text, generate narration
(`scripts/generate_ryskulov_narration.py`'s pattern), generate the
Remotion `scenesData.ts` from measured audio
(`scripts/generate_ryskulov_scenes_data.py`'s pattern), run a pre-render
checklist before any full render (CLAUDE.md section 10), then render and
deliver (`scripts/append_studio_outro.py`,
`scripts/kaggle_dataset_upload.py`).

## Scripts of note

- `scripts/validate.py` — schema + cross-reference validation across the
  whole repo. Run it after every meaningful change; should always report
  0 errors before you consider a work block done.
- `scripts/kaggle_dataset_upload.py` — safe add/replace-one-file upload to
  a shared Kaggle dataset (downloads current file list, merges, re-uploads
  together, verifies by polling until the file's *size* matches, not just
  its presence — a real data-loss incident and a real false-failure bug
  are both documented in this file's docstring/history; don't call
  `kaggle datasets version` directly against a shared dataset).
- `scripts/append_studio_outro.py` — appends `brand/GOKUMAY_signature_outro.mp4`
  to a finished master render, letterboxing/pillarboxing to fit any canvas.
  Always the last production step.
- `scripts/sync_remotion_public.py` — regenerates a Remotion app's
  gitignored `public/{still,video,audio}` from `projects/<id>/assets/`
  (only safe when filenames match 1:1 — see its docstring).
- `scripts/pre_render_checklist_*.py` — per-project checklists (loop
  ratios, missing visuals, forbidden-content negative-prompt coverage,
  numeric fidelity). Write one for every new project before its first full
  render — see CLAUDE.md section 10 for why this is not optional.

## Upgrading

The bible versions as a unit. Replace `bible/`, `schemas/`, `templates/`,
`style/` and `prompts/` together; never overwrite `projects/`.

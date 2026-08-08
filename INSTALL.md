# INSTALL

## Requirements

- Python 3.9+
- Node 18+ (only needed once you actually render — `scripts/remotion_setup.sh` sets up a project's Remotion app)
- `ffmpeg` / `ffprobe` (audio/video duration measurement, outro concatenation, checklists)
- `poppler-utils` (`pdfinfo`, `pdffonts`, `pdftotext`, `pdfimages`) — only if a project's source is a PDF
- `kaggle` CLI, authenticated (`~/.kaggle/kaggle.json`) — only if you use `scripts/kaggle_dataset_upload.py` / `archive_to_kaggle.py`
- API access as needed per project: an LLM (Claude Code itself covers most of this), ElevenLabs (narration), Google Flow (image/video generation — most projects in this system's history have used the Flow *web UI* manually with Claude-Code-generated prompts, not the API)

## Steps

```bash
unzip gokumay_studio_os.zip -d my-studio
cd my-studio
bash scripts/install.sh
cp .env.example .env      # fill in real keys - .env is gitignored
python3 scripts/validate.py
```

`scripts/install.sh` creates the directory scaffold, checks for required
tools, and installs Python dependencies from `requirements.txt`.

## Start a project

```bash
mkdir -p projects/PRJ-myproject/input
cp projects/project.example.json projects/PRJ-myproject/project.json
# edit: project_id, title, source.file + sha256, rights.source_basis,
#       template_ref, language, budget
sha256sum projects/PRJ-myproject/input/<source-file>
```

`rights.source_basis` must not stay `unknown` — the system halts on it by
design (Module 12 §11).

```bash
scripts/remotion_setup.sh PRJ-myproject
cd remotion_myproject && npm install
```

## Using it with Claude Code

Open the repository root in Claude Code — it will read `CLAUDE.md`
automatically at the start of a session. To kick off a new project, tell
it something like:

> Read CLAUDE.md, then Module 13 and Module 14. Ingest
> projects/PRJ-myproject/input/<source-file> according to Module 14, adapt
> scripts/scaffold_ryskulov_project.py's pattern into a scaffold script for
> this project, and emit scenes/, prompts_used/, and a project.json
> decisions_log entry explaining your template/style choices.

Claude Code will load bounded context, validate its output against
`schemas/`, and write only to this project's own owned paths (Single
Writer law — CLAUDE.md law #2).

## Upgrading

The bible versions as a unit. Replace `bible/`, `schemas/`, `prompts/`,
`templates/` and `style/`; never overwrite `projects/`.

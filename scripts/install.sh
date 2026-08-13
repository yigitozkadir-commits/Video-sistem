#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "AI Audiobook Studio OS v2.0 — setup"
echo "Root: $ROOT"

for d in bible schemas prompts prompts/axes templates style projects scripts \
         kernel agents adapters knowledge; do
  mkdir -p "$d"
done

# per-project scaffold template
mkdir -p projects/_scaffold/{input,extracted,ocr,beats,scenes,decisions,prompts_used,\
assets/{video,image,audio,reference},timeline,render,qa,reports,logs,state,graph,output}
echo "project scaffold ready at projects/_scaffold"

missing=0
for t in python3 ffmpeg ffprobe pdfinfo pdffonts; do
  if command -v "$t" >/dev/null 2>&1; then echo "  ok   $t"
  else echo "  MISS $t"; missing=1; fi
done
[ "$missing" -eq 1 ] && echo "Some tools are missing; ingest/render will be limited."

if command -v node >/dev/null 2>&1; then
  echo "  ok   node $(node -v)"
else
  echo "  MISS node - required for Remotion rendering (see remotion_template/, scripts/remotion_setup.sh)"
fi

if command -v kaggle >/dev/null 2>&1; then
  echo "  ok   kaggle CLI"
else
  echo "  MISS kaggle CLI - only needed for scripts/kaggle_dataset_upload.py / archive_to_kaggle.py (pip install kaggle)"
fi

if [ -f requirements.txt ]; then
  echo
  echo "Installing Python dependencies from requirements.txt..."
  python3 -m pip install -r requirements.txt || \
    echo "  pip install failed - install manually: pip install jsonschema elevenlabs python-dotenv Pillow"
fi

echo
echo "counts:"
echo "  bible modules : $(ls bible/Module_*.md 2>/dev/null | wc -l)"
echo "  schemas       : $(ls schemas/*.json 2>/dev/null | wc -l)"
echo "  templates     : $(ls templates/*.json 2>/dev/null | wc -l)"
echo "  style profiles: $(ls style/*.json 2>/dev/null | wc -l)"
echo "  prompts       : $(ls prompts/PV-*.json 2>/dev/null | wc -l)"
echo "  scripts       : $(ls scripts/*.py 2>/dev/null | wc -l)"
echo
[ -f .env ] || { [ -f .env.example ] && cp .env.example .env && echo ".env created from .env.example - fill in real keys before generating narration/images"; }
echo
echo "Next: python3 scripts/validate.py   then open CLAUDE.md"
echo "Starting a new project's Remotion app: scripts/remotion_setup.sh PRJ-<id>"

#!/bin/bash
# Sets up a new project's Remotion app by copying the studio's standard
# composition skeleton (remotion_template/ - crossfade + Ken-Burns + measured
# narration audio, with the interpolate() short-slot guard fixes baked in
# from real production incidents). Do not scaffold a Remotion project from
# scratch (create-remotion et al.) - it won't have those fixes.
#
# Usage: scripts/remotion_setup.sh <project_id>
# Example: scripts/remotion_setup.sh PRJ-myproject
#   -> creates remotion_myproject/ (project_id lowercased, PRJ- prefix dropped)

set -e

PROJECT_ID="${1:?Usage: scripts/remotion_setup.sh <project_id>, e.g. PRJ-myproject}"
DIR_NAME="remotion_$(echo "$PROJECT_ID" | sed 's/^PRJ-//' | tr 'A-Z' 'a-z' | tr '-' '_')"

echo "Remotion setup for $PROJECT_ID -> $DIR_NAME"
echo "============================================"

if ! command -v node &> /dev/null; then
    echo "Node.js not found. Install Node.js 18+: https://nodejs.org"
    exit 1
fi
echo "ok   node $(node -v)"
echo "ok   npm  $(npm -v)"

if [ -d "$DIR_NAME" ]; then
    echo "ERROR: $DIR_NAME already exists - not overwriting. Remove it first if you want a clean re-copy."
    exit 1
fi

cp -r remotion_template "$DIR_NAME"
rm -f "$DIR_NAME/public/still/.gitkeep" "$DIR_NAME/public/video/.gitkeep" "$DIR_NAME/public/audio/.gitkeep"
echo "copied remotion_template/ -> $DIR_NAME/"

# Rename the placeholder identifiers to match this project.
sed -i.bak "s/remotion_template/$DIR_NAME/" "$DIR_NAME/package.json" && rm -f "$DIR_NAME/package.json.bak"

echo ""
echo "Next steps:"
echo "  1. cd $DIR_NAME && npm install"
echo "  2. Scaffold the project's scenes: adapt scripts/scaffold_ryskulov_project.py"
echo "     (or scaffold_baskurtlar_project.py) into scripts/scaffold_$(echo "$PROJECT_ID" | sed 's/^PRJ-//' | tr 'A-Z' 'a-z')_project.py"
echo "  3. Generate narration: adapt scripts/generate_ryskulov_narration.py"
echo "  4. Regenerate src/scenesData.ts from measured audio: adapt"
echo "     scripts/generate_ryskulov_scenes_data.py (narration is the clock - CLAUDE.md law #3)"
echo "  5. Sync assets into public/: python3 scripts/sync_remotion_public.py $PROJECT_ID $DIR_NAME"
echo "     (only if public/{still,video,audio} filenames match projects/$PROJECT_ID/assets/ 1:1 -"
echo "     otherwise assets need a selection/rename step during ingestion, see CLAUDE.md's sync script docstring)"
echo "  6. Rename the composition id in $DIR_NAME/src/Root.tsx away from the generic"
echo "     'studio-video' if you want a project-specific id, and update package.json's"
echo "     render script + any CI matrix entry to match."
echo "  7. Before a FULL render: run scripts/pre_render_checklist_ryskulov.py's pattern"
echo "     adapted for this project (CLAUDE.md section 10 - never skip this)."
echo "  8. Render: cd $DIR_NAME && npx remotion render src/index.ts <composition-id> ../output/master.mp4 --concurrency=4"
echo "  9. Append the studio outro: python3 scripts/append_studio_outro.py output/master.mp4 output/master_with_outro.mp4"

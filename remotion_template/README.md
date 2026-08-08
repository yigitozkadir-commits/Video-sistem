# remotion_template

Studio-standard Remotion composition skeleton — do not render from this
directory directly. Copy it per project instead:

```
scripts/remotion_setup.sh PRJ-<project_id>
cd remotion_<project_id>
npm install
```

What's here and why:

- `src/compositions/StudioComposition.tsx` — the crossfade + Ken-Burns +
  measured-narration-audio pattern, with the `interpolate()` short-slot
  guard that has caused two real render crashes in this studio's history
  (see the comment at the top of the file). Rename the component/file per
  project if you like; keep the guard.
- `src/scenesData.ts` — the shape every `scripts/generate_<project>_scenes_data.py`
  writes. Regenerate it from measured `assets/audio/NAR-SC-*.wav` durations
  once a project has real narration (narration is the clock — CLAUDE.md
  law #3). Never hand-estimate scene duration once audio exists.
- `src/Root.tsx` — composition id defaults to `studio-video`; rename it
  once copied if you want a project-specific id (keep `package.json`'s
  `render` script and any CI matrix entry in sync).
- `public/{still,video,audio}/` — empty on purpose (`.gitkeep` only).
  Populate via `scripts/sync_remotion_public.py <project_id> <remotion_dir>`
  once a project's `projects/<id>/assets/` exist, or gitignore this and
  regenerate it after every clone (see `CLAUDE.md` section 9 for the
  reasoning — these are regenerable copies, never the source of truth).

Before a full render, always run this project's own pre-render checklist
(adapt `scripts/pre_render_checklist_ryskulov.py`'s pattern) — see
`CLAUDE.md` section 10. A defect caught in `scenesData.ts` costs nothing to
fix; the same defect caught in a finished `.mp4` costs a full re-render.

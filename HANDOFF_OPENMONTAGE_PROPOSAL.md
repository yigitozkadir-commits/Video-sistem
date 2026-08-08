# HANDOFF: OpenMontage-inspired improvements to Gök Umay AI Audiobook Studio OS

**Read this with zero other context.** This file is meant to be copied to a
different Claude Code account/session working on a separate clone of the
same "Gök Umay AI Audiobook Studio OS" repository, so that account can
implement the same changes and both repos stay in sync. It assumes nothing
from any prior conversation.

**What this repo is:** a Remotion-based (React video-rendering) AI
audiobook/documentary video production system, governed by `CLAUDE.md` at
the repo root (read that first — it defines the 8 operating laws this
whole document assumes: contract-over-prose, single-writer-per-path,
narration-is-the-clock, no-silent-degradation, deterministic-replay,
cost-is-a-constraint, human-gates-as-objects, fail-loud-resume-cheap).
`bible/*.md` (22 modules) are the system's specs; `schemas/*.json` are the
JSON Schema contracts every inter-agent artifact validates against;
`scripts/` is the Python tooling; `templates/` and `style/` are production
presets; `projects/<id>/` are per-project working directories.

---

## 1. What existed before this round of work

A prior session set up the studio from a zip archive (bible + schemas +
scripts + templates + style profiles), reported which API keys were
missing (ElevenLabs, Flow/Gemini — none were configured at the time), and
made no functional changes beyond scaffolding.

A second round reviewed an uploaded findings document and fixed 8 real
issues after verifying each against the actual code (not trusting the
document blindly):

- **B-01**: fixed a race condition in the shared ID-counter helper
  (`scripts/lib/id_counter.py`) — concurrent callers could allocate the
  same ID.
- **B-02**: deduplicated a `probe_duration()` (ffprobe wrapper) that had
  been copy-pasted identically across 5 scripts into one shared
  `scripts/lib/checklist_common.py`.
- **B-03**: fixed `scripts/validate.py`'s bible-module range check.
- **B-04**: built the first unit test suite (stdlib `unittest`, no pytest
  dependency) covering the pure/deterministic pieces of the codebase.
- **B-05**: implemented captions end-to-end — `schemas/caption_track.schema.json`,
  `scripts/generate_captions.py` (word-level timing → phrase-chunked
  captions via `@remotion/captions`), and `StudioComposition.tsx` rendering
  (opt-in per scene via a `captions` field, default off).
- **B-06**: wired `elevenlabs_client.py`'s `generate_music()` to
  ElevenLabs' real Music API (`client.music.compose`) — it had been a
  manual-generation stub because the API didn't exist yet when first
  written.
- **B-07**: built `scripts/lib/flow_pool.py`, account-pool bookkeeping for
  Flow's 10-account rotation (daily video-seconds cap, round-robin,
  fallback-to-still on exhaustion).
- **B-08**: unified the `scripts/lib/*` import convention across all
  scripts (some used relative imports, some absolute — picked one and
  applied it everywhere).

All of this is verified by `python3 scripts/validate.py` (0 errors) and
`python3 -m unittest discover -s tests` (61/61 passing at that point).

**PRJ-ninniler-atlasi** ("Ninniler Atlası" — a 22-video lullaby project,
one video per Turkic ethnic lullaby tradition) was then built: sourced
academic text from two `.docx` research compilations, pulled a Kaggle
image inventory (`ninniler-iin-grsel-envanter` + a second `ninniler-part2`
dataset the user uploaded mid-project), and — per an explicit user
decision — reused existing images across tonally-similar lullabies rather
than generating new art for every one of the 22 nations (own
geo-specific shots + tonally-close sibling-nation shots + a shared
universal mother/cradle/infant pool; full per-nation breakdown in
`projects/PRJ-ninniler-atlasi/decisions/0002_remaining12_image_reuse.md`).
All 22 lullaby videos were rendered as silent, placeholder-timed
slideshows (`remotion_ninniler_atlasi/src/lullabies.ts` — 20 stills ×
4.5s each, `IMAGE_DURATION_S` explicitly marked PLACEHOLDER pending real
music) and uploaded to Kaggle as datasets. Music has not been added yet —
that is separate, ongoing work outside this handoff's scope. A **plan-mode
only** brainstorm also happened about whether a planned ~3-hour final
loop-video (repeating a ~3-minute music+visual cycle) needs a full
from-scratch render or can be built via render-once + `ffmpeg`
concat-list loop-extend; that plan was never approved/executed and is not
part of this handoff.

---

## 2. OpenMontage research summary

The user asked for research into [OpenMontage](https://github.com/calesthio/OpenMontage)
(AGPL-3.0 — an agent-orchestration framework: Markdown "skill" files +
YAML "pipeline" definitions that turn an AI coding assistant into a video
production studio) to evaluate whether it, or ideas from it, could improve
this studio.

**License note (important):** OpenMontage is AGPL-3.0. Nothing below
involved copying or adapting any of its code. Every "adopt/adapt"
recommendation is a clean-room reimplementation of a publicly-documented
architectural *idea*, built independently against this repo's own
schemas/conventions.

Findings:

- **12 named pipelines** (documentary-montage, animated-explainer,
  talking-head, cinematic, etc.), each declared in YAML with: stages,
  `required_artifacts_in`/`produces`, checkpoint policies,
  `budget_default_usd`, `max_revisions_per_stage`, and — notably —
  **`max_wall_time_minutes`**, a wall-clock ceiling this studio's
  `retry`/`budget` config didn't have an equivalent of.
- Its own Remotion engine (`remotion-composer/`) with a documented
  `SCENE_TYPES.md` defining 4 scene categories this studio doesn't have:
  typography cards, **data visualization** (BarChart/LineChart/PieChart/
  KPIGrid), **UI simulation** (TerminalScene/ScreenshotScene), and reveal
  overlays.
- **Archival image/footage sourcing**: pulling from Archive.org/NASA/
  Wikimedia Commons by semantic query, as an alternative or complement to
  AI-generated illustration — public-domain sourcing solves the rights
  chain for free where it applies.
- **Zero-API-key mode**: Piper TTS (local/free) + free stock sources as a
  complete fallback path when no paid keys are configured.
- **Slideshow-risk scoring**: a pre-render check for "this content is more
  static/repetitive than it should be."
- **Multi-axis provider scoring with an auditable trail**: scoring
  providers across 7 named axes (task fit, quality, control, reliability,
  cost, latency, continuity) with a recorded rationale.

---

## 3. The 7-idea evaluation (adopt/adapt/skip, with reasoning)

1. **Archival image/footage sourcing — ADOPT, highest value.** Solves two
   problems at once: visual variety for documentary/historical content,
   and this studio's `rights.source_basis: "public_domain"` value (which,
   before this, was never actually produced by anything — Flow generation
   was the only visual source). Scoped to the documentary/historical
   project line (Avrasya, Ryskulov, future projects); not forced onto
   Ninniler Atlası's watercolor-illustration aesthetic.
2. **Wall-clock timeout — ADOPT, confirmed real gap.** Before this work,
   only attempt-count (`studio.config.json`'s `retry` block) and dollar
   budget (`project.json`'s `budget`) bounded anything — nothing bounded
   *how long* a retry loop could keep sleeping and retrying. Cheap,
   additive.
3. **Slideshow-risk scoring — ADOPT, but must be style-relative.** Several
   projects (Ninniler Atlası) are *intentionally* slideshows
   (`motion_ceiling: 1-2` by template design) — a blind "this is static"
   flag would misfire on all of them. The real signal: a scene more
   static/repetitive than its OWN style profile and template call for.
4. **Piper TTS fallback — ADOPT, but draft-quality-only, never silent.**
   ElevenLabs quota exhaustion has hit this studio mid-batch three
   separate times (`scripts/lib/production_ledger.py`'s own docstring).
   But final delivery quality must never silently degrade — default
   `draft_only`, promotion to a delivered master requires a human
   decision (law #4).
5. **Multi-axis provider scoring — ADAPT, low priority, sequenced last.**
   `decision.schema.json` already requires `reason` +
   `alternatives_rejected` (M17 §3) — what was missing was just a named
   rubric. Deliberately built AFTER items 1 and 4 landed, since scoring
   providers needs real second providers to compare against (before this
   work, visual sourcing = Flow only, audio = ElevenLabs only).
6. **Data-viz / UI-simulation scene types — SKIP (for now), documentation
   only.** No current or planned project is an explainer-style video. Real
   React/chart engineering plus a new `SceneVisual` variant for zero
   consumers is speculative engineering. One paragraph in the bible
   records this as a deliberate scoping decision, not an oversight.
7. **Declarative YAML pipeline definitions — SKIP, the existing instinct
   was right.** This studio's imperative `scaffold_<project>_project.py`
   pattern has a proven production history across 5 finished + 2
   in-progress projects. Rewriting the whole system's backbone risks a lot
   for uncertain gain, and arguably conflicts with law #1 ("contract over
   prose") — nothing would guarantee the YAML and the Python stayed in
   sync.

---

## 4. Changes implemented in this repo

All items below are verified together: `python3 scripts/validate.py`
reports **0 errors** (37 schemas, 22 bible modules, 101 JSON files
parsed), and `python3 -m unittest discover -s tests` reports **131/131
tests passing**, after this round of work.

### 1.1 Archival image/footage sourcing
- **Extended** (not rewritten from scratch) `scripts/find_reference_images.py`
  from Wikimedia-Commons-only to a 3-provider search: Wikimedia Commons,
  NASA Images (`images-api.nasa.gov`), Archive.org
  (`archive.org/advancedsearch.php`). A shared `license_is_reusable()` gate
  rejects NC/ND/unclear licenses uniformly across all three — importantly,
  each provider's ambiguous case defaults to **rejection**, never assumed
  reusable: NASA results credited to a named non-NASA photographer, and
  Archive.org items with no `licenseurl` at all, are both treated as
  unclear and skipped rather than guessed-safe. Verified against live
  results in this session: Wikimedia and NASA both returned valid
  candidates; Archive.org correctly rejected an item for missing license
  metadata.
  - *Course-correction note:* the original plan named a new script,
    `find_archival_footage.py`. Before writing it, the existing
    `find_reference_images.py` was read in full and found to already do
    substantially the same thing — so the actual implementation extends
    that file instead of duplicating it. Flagging this explicitly since it
    means the real diff differs from the plan's literal filename.
- **New schema** `schemas/archival_asset.schema.json` — `source` (enum:
  wikimedia_commons/nasa/archive_org), `source_url`, `license`, `sha256`,
  `retrieved_at`, etc. Validated against a constructed sample via
  `jsonschema.validate()`.
- **New template** `templates/TPL-archival-documentary.json` — extends
  `TPL-documentary`, adds an `asset_sourcing` field prioritizing archival
  footage over Flow generation (mirrors the existing
  `flow_account_pool.fallback_to_still` shape, priority reversed).
  `budget_profile.credits_per_minute` halved (180→90) versus its parent,
  explicitly marked as an *unmeasured planning estimate* in its own
  `source_note`, not a measured constant.
- **Bible:** `bible/Module_09_Asset_Management_and_Metadata.md` §8b
  (generated reference vs. sourced archival asset); short cross-reference
  added to `bible/Module_06_Google_Flow_Production_Guide.md` §1.

### 1.2 Wall-clock timeouts + stale human gates
- `studio.config.json` gained a `timeouts` block — per-queue minute
  ceilings using the same `q.*` keys as `concurrency` (`q.render: 90`,
  comfortably above CLAUDE.md §10's documented legitimate 45-60min render
  range, so it catches genuine runaways, not normal-but-slow renders).
- `scripts/lib/retry.py`'s `with_retry()` gained an optional `queue=`
  parameter: tracks `time.monotonic()` across the whole retry loop
  (attempts + backoff), raises a new `WallClockExceeded` (logged as
  `E-SYS-221`) if cumulative time exceeds the queue's configured ceiling —
  **before** attempt-count exhaustion would otherwise trigger. This bounds
  the loop, not a single hung call — a `fn()` with no timeout of its own
  (e.g. a bare subprocess) still needs its own timeout at the call site;
  the docstring says so explicitly.
- **New script** `scripts/check_stale_human_gates.py` — scans every
  project's `state/approvals.jsonl` for `decision: "pending"` records
  older than `studio.config.json`'s `human.approval_sla_hours` (a
  documented-but-previously-unimplemented gap — bible §9/D3 already
  specified this failure mode, confirmed via grep that zero scripts ever
  checked it, and zero `approval.schema.json` instances have ever actually
  been created in this repo). Reports which pending gates are stale and
  what the `on_timeout` policy is — it detects and reports, it does not
  autonomously apply the policy (CLAUDE.md §3: an agent may never decide a
  gate verdict).
- **Bible:** `bible/Module_13_AI_Production_Operating_System.md` §10
  (new "Wall-clock ceiling" and "D3's approval wait" subsections), §17
  (Halt Conditions note that a stale gate is advisory, not an autonomous
  HALT).

### 1.3 Slideshow-risk scoring (style-relative)
- **New** `scripts/lib/slideshow_risk.py` with three checks, all measured
  relative to the project's OWN `templates/*.json` (`director.pace`) and
  `style/*.json` (`motion_ceiling`) — never an absolute "this looks
  static" threshold:
  1. Per-visual-slot duration vs. the project's template's declared pace
     range (with tolerance, same "last slot absorbs rounding" philosophy
     as the existing `LOOP_RATIO_THRESHOLD` pattern).
  2. Back-to-back identical assets (by filename, then by sha256 for
     same-bytes-different-name) across adjacent visual slots — not
     style-relative, a repeated frame is always a defect.
  3. Style `motion_ceiling` vs. the actual `KEN_BURNS_SCALE` constant
     baked into `StudioComposition.tsx` — flags when a style intends more
     motion (`motion_ceiling > 1`) than the render's still-restrained
     Ken-Burns constant actually delivers.
  - Handles two real, differently-shaped data files in this repo
    (`scenesData.ts`'s flat `SCENES` array vs. `lullabies.ts`'s nested
    `LULLABIES[].scenes[]`) that disagree on field order between
    `durationFrames` and `visuals` — the parser is order-agnostic by
    construction rather than assuming one.
  - **Real-data validation, not synthetic:** run against
    `PRJ-ninniler-atlasi`'s actual `lullabies.ts` (22 lullabies, 20 slots
    each), it produces exactly one real finding — Ninniler's style profile
    declares `motion_ceiling: 2` but the render's `KEN_BURNS_SCALE` is
    still `1.03` (the constant's own code comment says it's calibrated
    for `motion_ceiling: 1`) — and zero false positives on the other two
    checks.
- **New** `scripts/pre_render_checklist_ninniler.py` — this project had no
  pre-render checklist script at all before this (CLAUDE.md §10 requires
  one before a project's first full render; Ninniler hasn't had one yet).
  Wired into the existing three legacy checklist scripts
  (`pre_render_checklist.py`/`_avrasya.py`/`_ryskulov.py`) as an
  additional guarded check, same call pattern as their existing
  `check_video_loop_ratios()`.
- **Bible:** `bible/Module_12_AI_Quality_Assurance_Bible.md` §6, one
  paragraph, explicit that this is advisory and style-relative, not a T1
  gate.

### 1.4 Piper TTS draft-only fallback
- **New** `scripts/lib/tts_providers.py` — a `TTSProvider` shape
  (documentation, not an enforced ABC — `ElevenLabsStudio` already
  duck-types into it without modification, respecting single-writer per
  file) plus `select_tts_provider()`: tries `ElevenLabsStudio()` first,
  falls back to Piper **only if** `studio.config.json`'s
  `narration.fallback.enabled` is true **and** ElevenLabs itself failed to
  initialize (missing SDK or `ELEVENLABS_API_KEY`) — never an
  unconditional substitution, and always with a printed/logged notice.
- **New** `scripts/piper_client.py` — wraps the local `piper` binary
  (`PIPER_BINARY`/`PIPER_MODEL_PATH` env vars), same cache/cost-ledger
  pattern as `elevenlabs_client.py` (separate cache index file, provider
  `"other"` in the cost ledger since Piper has no dedicated enum value and
  the schema wasn't changed for it — genuinely `cost: 0`, not a guessed
  price). Every result carries `quality_gate: "draft_only"`. Piper itself
  is not installed in this sandbox, so tests mock `subprocess.run` —
  matching this repo's existing convention for external calls that can't
  run in-sandbox.
- `voice_request.schema.json`'s existing free-text `model` field already
  carries `"piper:<model-stem>"` with **no schema change needed** —
  deterministic replay is preserved regardless of which provider actually
  produced a take.
- `studio.config.json` gained a `narration.fallback` block, same shape
  family as the existing `flow_account_pool.fallback_to_still`.
- **Bible:** `bible/Module_16_ElevenLabs_Enterprise.md` new §1b (Local
  Fallback), explicit that `draft_only` may never be silently promoted to
  a delivered master; `Module_13` §17's "degrade instead of halt" list
  updated with this as a concrete example.

### 1.5 Multi-axis provider scoring rubric
- `schemas/decision.schema.json` gained an **optional** `scoring.axes`
  object — six named axes (`cost`, `quota_risk`,
  `quality_for_style_profile`, `rights_basis_strength`,
  `determinism_replay_cost`, `latency`), each 0-1 where **1.0 is always
  the more favorable end** (e.g. `cost: 1.0` means cheapest, not
  expensive — direction is fixed so scores can be compared without
  per-axis sign confusion). Own axis set, not OpenMontage's 7 copied
  verbatim. `additionalProperties: true` throughout, so this never breaks
  an existing decision record. Validated via `jsonschema.validate()`
  against a constructed sample.
- **Bible:** `bible/Module_17_AI_Director.md` new §3b, with a direction
  table and an explicit note that `question`'s fixed enum still has no
  "provider_choice" value — a comparison that doesn't fit an existing
  `question` still uses the `decisions/*.md` free-form-note escape hatch
  (same pattern as `decisions/0001_rights_basis.md`); `scoring` is the
  shape to reach for once such a comparison is attached to an actual
  schema-bound decision object.
- Deliberately sequenced **after** 1.1 and 1.4 landed — before this round
  of work there was only one visual provider (Flow) and one audio
  provider (ElevenLabs), so a scoring rubric had nothing real to compare.

### 1.6 Documentation-only note (skipped item)
- `bible/Module_11_Remotion_Production_Pipeline.md` new §5b: records that
  data-visualization and UI-simulation scene types are a deliberately
  deferred extension point (no consumer project needs them yet), not an
  oversight. No code change — this is item 6 from the evaluation above.
- Item 7 (YAML pipelines) has no separate doc — this handoff file and the
  session's approved plan file are that decision's record.

---

## 5. Sync note

Both accounts working on this system should follow the **same priority
order** implemented here: 1.1 → 1.2 → 1.3 → 1.4 → 1.5 → 1.6, since later
items depend on earlier ones landing first (1.5 explicitly needs 1.1 and
1.4's real second-providers to have anything to score). If either
account's implementation of an item ends up diverging from what's
described in Section 4 above — different file names, a different
threshold, a different schema shape — **update this section of this file**
and re-share it, rather than letting the two repos silently drift into two
different sources of truth for the same decision (this is the same
"contract over prose" principle, law #1, applied to keeping two
independent implementations honest about what actually shipped where).

Files touched, for a quick diff-against-checklist:

| File | Change |
|------|--------|
| `HANDOFF_OPENMONTAGE_PROPOSAL.md` | new (this file) |
| `schemas/archival_asset.schema.json` | new |
| `schemas/decision.schema.json` | optional `scoring` field added |
| `templates/TPL-archival-documentary.json` | new |
| `scripts/find_reference_images.py` | extended: 3 providers (was Wikimedia-only) |
| `scripts/check_stale_human_gates.py` | new |
| `scripts/lib/retry.py` | wall-clock `queue=` param + `WallClockExceeded` |
| `scripts/lib/slideshow_risk.py` | new |
| `scripts/pre_render_checklist_ninniler.py` | new |
| `scripts/pre_render_checklist.py` / `_avrasya.py` / `_ryskulov.py` | slideshow-risk check wired in |
| `scripts/lib/tts_providers.py` | new |
| `scripts/piper_client.py` | new |
| `studio.config.json` | `timeouts` + `narration.fallback` blocks added |
| `bible/Module_06`, `Module_09`, `Module_11`, `Module_12`, `Module_13`, `Module_16`, `Module_17` | cross-references / new subsections |
| `tests/test_find_reference_images.py`, `test_retry.py` (extended), `test_check_stale_human_gates.py`, `test_slideshow_risk.py`, `test_piper_client.py`, `test_tts_providers.py` | new/extended test coverage |

**Verification command for the receiving account, after implementing:**
```
python3 scripts/validate.py                    # expect: 0 errors
python3 -m unittest discover -s tests           # expect: all passing
```

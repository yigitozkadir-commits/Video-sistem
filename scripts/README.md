# Production Scripts — Cost & Time Notes

Two concrete lessons from producing the Gök Umay Atlas videos (6 videos,
141-page source PDF), where token cost and wall-clock time were the
actual bottleneck — not anything a vague roadmap could fix.

## 1. Classify PDF pages before reading any of them as images

`classify_pdf_pages.py` — the single biggest cost driver in that session
was reading full-resolution page renders through the vision model just to
figure out "is this page a portrait or an article?" For a ~140-page PDF
that's ~140 image reads before any real work starts.

Fix: run `pdftotext` per page first (cheap, no vision tokens) and classify
by extracted character count. Portrait/illustration pages in a
decorative-frame atlas layout carry no body text; article pages do. This
was verified against 20 pages already hand-classified by eye and matched
100%.

```bash
python3 scripts/classify_pdf_pages.py <pdf> <first_page> <last_page>
```

Only render/read the pages the script marks `IMAGE` — skip full-image
reads entirely for anything marked `TEXT`.

## 2. Narration generation is now cache-first and quota-aware

`scripts/lib/production_ledger.py` — `ElevenLabsStudio.text_to_speech()`
(in `scripts/elevenlabs_client.py`) now does this automatically for every
caller, no per-script changes needed:

- **`ArtifactCache`**: fingerprints `(text, voice_id, model_id, stability,
  similarity, style)` with sha256. If a matching output already exists,
  it's reused and the API is never called. This is what made the Video 5
  quota-exhaustion retry safe to just re-run instead of hand-trimming the
  figure list to "the ones that didn't finish."
- **`CostLedger`**: appends every call (hit or miss, success or failure)
  to `projects/<id>/state/cost_ledger.jsonl` in
  `schemas/cost_ledger.schema.json` shape, and checks a known per-key
  quota (`ELEVENLABS_QUOTA_CHARS`, default 10000 — ElevenLabs' free-tier
  character cap) *before* calling the API. Across this project the same
  failure happened three times: a batch would run partway through, hit
  401 quota_exceeded, and only then reveal the account was out of
  credits. The pre-flight check turns that into an immediate, actionable
  `RuntimeError` instead of a wasted request.

`scripts/write_render_manifest.py` writes a
`schemas/render_manifest.schema.json`-compliant record (sha256, codec,
resolution, timing) for a finished render to
`projects/<id>/state/render_manifest.jsonl`. This is what makes `studio
why <artifact>` (CLAUDE.md §8) actually answerable from a file instead of
from a chat scrollback: every one of the 7 renders in this project
(6 atlas videos + the fairytale master) now has one.

## 3. Retry actually implements studio.config.json's existing contract

`studio.config.json` has had a `retry` block (`transient_max`,
`generation_max`, `backoff_base_s`, `backoff_cap_s`, `jitter`) since the
system was scaffolded, but nothing in the codebase read it - every call
was single-attempt. `scripts/lib/retry.py` (`with_retry`) reads those
exact values and applies exponential backoff + jitter, capped at
`backoff_cap_s`.

The one thing it deliberately does *not* retry: quota/payment errors.
Retrying a 401 quota_exceeded just spends another request against a wall
that isn't moving - CLAUDE.md law #6 ("budget exhaustion halts
production") means that class of failure should fail fast, not back off.
Callers raise `NonRetryable` (or the ElevenLabs client's quota-detection
does it for you) to route around the backoff loop. Verified with a unit
test (non-retryable fails on attempt 1, transient failures retry twice
then succeed on schedule) and a live regression call through
`elevenlabs_client.py`.

## 4. Feature flags and a production report

`scripts/lib/feature_flags.py` — `is_enabled("name")`, checked via
`FLAG_NAME=1` env var or `studio.config.json`'s `feature_flags` object.
Currently wired to one real flag: `FLAG_SKIP_CACHE=1` forces
`elevenlabs_client.py` to regenerate even when a cache hit exists (useful
when deliberately re-recording a scene with the same text but wanting a
fresh take).

`scripts/production_report.py` reads every project's cost ledger, render
manifest, and error log and prints cache-hit rate, units consumed, render
success/size, and any error needing human action per project - the
"Monitoring" item from the docs, as a script you run rather than a
dashboard that doesn't exist:

```bash
python3 scripts/production_report.py
```

## 5. Errors are now records, not just exceptions

`scripts/lib/errors.py` writes `schemas/error.schema.json`-compliant rows
to `projects/<id>/state/errors.jsonl`. `with_retry()` (in `retry.py`) takes
an optional `error_context` and logs automatically when a call ultimately
fails - `elevenlabs_client.py` is wired with `E-BUD-001` (quota wall,
`escalate_to: human`) and `E-GEN-001` (transient retries exhausted). This
is the actual scope of "Retry Intelligence"/"Dead Letter Queue" for a
single-writer sequential pipeline: a schema-shaped record of what gave up
and why, not a queue service with nothing to consume it.

## 6. Asset and run manifests — "studio why" answered from files

Two schemas existed in `schemas/` since the bible was scaffolded and were
never populated: `asset_manifest.schema.json` and `run_manifest.schema.json`.

- `scripts/write_asset_manifest.py [PRJ-id]` — hashes and type-classifies
  every real asset (stills, narration audio, delivered renders) into
  `projects/<id>/state/asset_manifest.json`. Reuses sha256 already computed
  in `render_manifest.jsonl` / the audio cache index instead of re-hashing
  large files.
- `scripts/write_run_manifest.py --backfill` — writes
  `projects/<id>/state/run_manifest.jsonl`, one entry per `run_id` already
  present in `render_manifest.jsonl` (model, version, bible_version, a
  fixed `global_seed: 0` since nothing in this pipeline is stochastic).

Together with `render_manifest.jsonl`, these three files answer CLAUDE.md
§8's test - "studio why output/atlas-video-1.mp4" - by chaining sha256 and
`run_id` across the three logs, no chat scrollback required.

## 7. Rendering via GitHub Actions — no wrapper script needed

`.github/workflows/render.yml` (`workflow_dispatch`, matrix over every
composition) is triggered and polled directly through the GitHub MCP
tools already available in this environment (`actions_run_trigger`,
`actions_get`, `get_job_logs`) — there's no separate "render broker"
script here, because I'm the only caller and I already hold the client.
Triggering a real run consumes GitHub Actions minutes (private repo, 2000
free min/month) and only happens with explicit go-ahead.

## 8. First project to actually populate scene/flow_shot_request schemas

`scripts/scaffold_baskurtlar_project.py` — one-time generator for
`projects/PRJ-baskurtlar-arastirma`. Earlier projects (fairytale, atlas)
never wrote `scenes/SC-*.json` or `state/scene_index.json` even though
`schemas/scene.schema.json` and `schemas/scene_index.schema.json` existed;
they used ad hoc Remotion-specific data files instead. This script writes
both the proper scene records and `prompts_used/<shot_id>/{image,video}.json`
as `schemas/flow_shot_request.schema.json`-compliant requests, reusing the
existing `flow.shot.wide.establishing` (PV-0044) / `flow.shot.closeup.realisation`
(PV-0031) prompt families instead of inventing new ones. It only writes
plan artifacts (prompts to hand to Flow) - no image/video generation
happens here, since this repo has no Flow API client (Flow generation is
external, same as the fairytale project's workflow).

## 9. Unit tests for the pure logic (`tests/`)

Schema validation (`scripts/validate.py`) checks contracts, not logic. The
deterministic-replay-critical functions that don't touch the filesystem or
a network - `ArtifactCache.fingerprint()`, `CostLedger.would_exceed_quota()`,
`retry.with_retry()`'s backoff/jitter math and `NonRetryable` short-circuit,
`checklist_common.long_compound_number_findings()`, and the
`lib/id_counter.py` lock (including an actual multi-process concurrency
test) - have stdlib `unittest` coverage in `tests/`. No pytest dependency;
run with:

```bash
python3 -m unittest discover -s tests
```

Run this after touching anything in `scripts/lib/` - it's seconds, not a
45-60 minute render, so there's no excuse to skip it (same "plan more,
render less" logic as CLAUDE.md section 10's pre-render checklist).

## 10. Flow account pool bookkeeping (`scripts/lib/flow_pool.py`)

`schemas/flow_account_pool.schema.json` defines the free-tier Google Flow
pool's quota shape (10 accounts × 3 videos/day × 10s/clip = 300s/day) but
had no reader/writer anywhere in the repo. This is bookkeeping only, not
automation - there's still no Flow API client here (section 8 above),
Flow generation stays a human pasting Claude-Code-written prompts into the
Flow web UI. What it replaces is tracking "which account, how much quota
left" by memory.

```python
from lib.flow_pool import FlowAccountPool

pool = FlowAccountPool(project_state_dir)
pool.init_new([                      # once per project, your real accounts
    {"account_id": "FLWACC-01", "email": "you1@example.com"},
    {"account_id": "FLWACC-02", "email": "you2@example.com"},
])

pool.reset_if_new_day()              # call before picking, clears yesterday's daily caps
account = pool.next_available_account()   # None -> fall back to still (studio.config.json fallback_to_still)
# ... paste the prompt into Flow web UI using `account`, get a clip back ...
pool.record_usage(account["account_id"], video_seconds=8)
```

Never invents an account roster - `init_new()` raises on an empty list.
Quarantine a banned/rate-limited account with `pool.quarantine(account_id,
reason)`; quarantined accounts stay out of rotation across day resets
until a human clears them.

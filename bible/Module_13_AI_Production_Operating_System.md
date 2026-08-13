# MODULE 13 — AI PRODUCTION OPERATING SYSTEM
**Version 2.0 · Layer 4 (Kernel) · Status: NORMATIVE**

> This is the kernel. Every other module is a process running on it.
> If a rule here conflicts with another module, this module wins — except for
> quality thresholds (M12) and creative authority (M17), which it delegates.

**⚠️ IMPLEMENTATION STATUS (added 2026-08-07, honest per law #4 - no silent
degradation):** §3-6, §9, §12-15 (task object, queue, worker system,
dispatcher, deadlock detection, JSON contracts including
`flow_shot_request/result.schema.json`, approval-lifecycle-as-object)
describe a
multi-worker, queue-driven kernel. In practice, every project shipped so far
(Başkurtlar, Dağların Uyuyan Devleri, Gök Umay Atlası, Fetih-1453, Avrasya
Bozkır Kuşağı) has run a simpler direct pipeline instead: Claude Code works
one task at a time per user request, no `task.jsonl` queue, no worker
registry, no `decisions/DEC-*.json` object has ever been written (the
`decisions/` folders exist in every project scaffold and are all empty), and
no `approval.schema.json` instance has ever been created — human sign-off
has happened as ordinary conversation turns, not as a stored object with
scope/expiry. This is not a defect in past work (M13 §23's automatic/human
boundary was honored in substance every time), but it means this module's
queue/worker/approval-object apparatus is currently **specified, not
exercised** - real if this studio ever needs concurrent multi-agent
production, dead weight otherwise. Read the rest of this module as the
design for that future, not a description of how things work today.

---

## 1. WHAT AN OS MEANS HERE

A guide tells a human what to do. An operating system tells a machine what is
*allowed* to happen. The difference is four things this module supplies:

1. **State** — a single authoritative description of where production is.
2. **Scheduling** — who works on what, in what order, with what resources.
3. **Contracts** — the only legal way for two agents to exchange information.
4. **Failure semantics** — what happens when reality disagrees with the plan.

Nothing in the pipeline may exist outside these four. An agent that "just knows"
something is a bug.

---

## 2. PRODUCTION STATE MACHINE

### 2.1 Project-level states

```
INIT ──► INGEST ──► ANALYZE ──► PLAN ──► GENERATE ──► ASSEMBLE ──► QA ──► EXPORT ──► ARCHIVE ──► COMPLETE
  │         │          │         │          │            │         │        │
  └─────────┴──────────┴─────────┴──────────┴────────────┴─────────┴────────┴──► HALTED ──► (human) ──► resume | ABORTED
```

**Transition law:** a state may only advance when *every* task belonging to it is
in `COMPLETED` or `SKIPPED(justified)`, and its exit gate (M12 §5) passed.

| State | Entry condition | Exit gate | Owner |
|-------|-----------------|-----------|-------|
| INIT | project.json validates | config lock | Kernel |
| INGEST | source file hash recorded | all inputs cataloged | Claude Code (M14) |
| ANALYZE | OCR confidence ≥ 0.92 avg | story graph complete | Orchestrator |
| PLAN | story graph approved | storyboard gate | AI Director (M17) |
| GENERATE | all prompts versioned | shot_accept per artifact | Flow (M15) / ElevenLabs (M16) |
| ASSEMBLE | all scene assets present | scene_accept | Remotion (M11) |
| QA | master rendered | master_export | Review Agent (M12) |
| EXPORT | QA pass | delivery manifest complete | Kernel |
| ARCHIVE | export verified | reproducibility check | Kernel |

### 2.2 Task-level states

```
PENDING → READY → ASSIGNED → RUNNING → REVIEW → { COMPLETED | RETRY_WAIT | FAILED | BLOCKED | CANCELLED }
                                                          │
                                                   RETRY_WAIT → READY (backoff elapsed)
```

- `PENDING` — created, dependencies unmet
- `READY` — dependencies satisfied, waiting for a worker
- `BLOCKED` — dependency failed permanently or awaiting human approval
- `REVIEW` — output produced, QA running (T1 then T2)
- `RETRY_WAIT` — failed, retry budget remains, backoff timer running

**Illegal transitions** (must raise `E-SYS-201`): RUNNING→READY,
COMPLETED→anything, FAILED→RUNNING without an approval object.

### 2.3 State is a file, not a memory

`state/production_state.json` is the single source of truth. It is written
**only** by the kernel, via atomic write (temp file + rename). Any agent that
needs state reads this file. An agent's internal belief about state is advisory
only and expires at the end of its turn.

---

## 3. TASK OBJECT (the atom of the system)

```json
{
  "task_id": "TSK-000412",
  "type": "flow.generate_shot",
  "project_id": "PRJ-taidula",
  "scene_id": "SC-014",
  "shot_id": "SH-014-03",
  "state": "READY",
  "priority": "P1",
  "owner_agent": "visual",
  "depends_on": ["TSK-000398", "TSK-000401"],
  "blocks": ["TSK-000420"],
  "input": { "spec_ref": "scenes/SC-014/shots/SH-014-03.json",
             "references": ["REF-CHR-001", "REF-ENV-004"] },
  "output": { "expected": ["assets/video/SH-014-03_v*.mp4"], "actual": [] },
  "determinism": { "model": "flow-video@2026-05", "seed": 774411, "prompt_version": "PV-0031" },
  "budget": { "estimated_credits": 30, "spent_credits": 0, "hard_cap": 60 },
  "attempts": 0,
  "max_attempts": 5,
  "retry_strategy_log": [],
  "checkpoint_ref": null,
  "created_at": "2026-08-05T09:12:00Z",
  "deadline": null,
  "qa_report_ref": null
}
```

Rules: a task owns exactly one artifact family; a task that would produce two
unrelated artifacts must be split; `depends_on` is a DAG edge and must never be
inferred at runtime — it is written at plan time.

---

## 4. QUEUE SYSTEM

Nine queues, each with its own concurrency limit, rate limit and cost profile:

| Queue | Concurrency | Rate limit source | Typical unit cost | Backpressure signal |
|-------|-------------|-------------------|-------------------|---------------------|
| `q.ingest` | 2 | local CPU | free | disk I/O wait |
| `q.ocr` | 4 | local/API | low | queue depth > 50 |
| `q.analysis` | 2 | LLM API | medium | token quota < 20 % |
| `q.prompt` | 4 | LLM API | low | — |
| `q.visual` | 3 | Flow quota | **high** | credits < 15 % |
| `q.voice` | 3 | ElevenLabs chars | medium | chars < 20 % |
| `q.music` | 1 | ElevenLabs | medium | — |
| `q.assemble` | 2 | local CPU/GPU | free | RAM > 85 % |
| `q.render` | 1–N | render farm | high | node saturation |
| `q.qa` | 6 | LLM/vision API | low | — |

**Queue laws**
1. A task enters exactly one queue, chosen by `type` prefix.
2. Queues are FIFO *within a priority class*, priority-preemptive across classes.
3. A queue at its concurrency limit does not reject — it holds. Rejection only on
   hard cap (queue depth > 500 → `E-SYS-310`).
4. Every queue publishes depth, wait time p50/p95, and failure rate every 30 s.
5. **Cost-heavy queues (`q.visual`, `q.render`) never run speculative work.**
   No shot is generated before its storyboard is gate-approved.

---

## 5. WORKER SYSTEM & OWNERSHIP

```json
{
  "worker_id": "WRK-visual-02",
  "role": "visual",
  "capabilities": ["flow.generate_shot", "flow.generate_still", "flow.upscale"],
  "state": "RUNNING",
  "current_task": "TSK-000412",
  "lease_expires_at": "2026-08-05T09:22:00Z",
  "heartbeat_at": "2026-08-05T09:14:30Z",
  "consumed": { "credits": 1240, "tasks": 37, "failures": 3 }
}
```

**Lease model.** A worker holds a task by lease, not by possession. Lease =
`estimated_duration × 2.5`, minimum 120 s. Heartbeat every 30 s. Missed
heartbeat × 3 → lease revoked, task returns to `READY`, attempt count **not**
incremented (infrastructure loss is not the task's fault — see M12 §14).

**Single Writer ownership (LAW-2):**

| Path | Sole writer |
|------|-------------|
| `input/` | nobody (immutable after ingest) |
| `extracted/`, `ocr/` | Claude Code |
| `scenes/*/spec` | Orchestrator + AI Director |
| `assets/video/`, `assets/image/` | Visual worker |
| `assets/audio/` | Audio worker |
| `timeline/`, `render/` | Assembly worker |
| `qa/` | Review agent |
| `state/`, `logs/` | Kernel only |

---

## 6. PRIORITY SCHEDULER

**Priority classes**

| Class | Meaning | Example |
|-------|---------|---------|
| P0 | Unblocks everything / safety | HALT handling, rights check, corrupted state repair |
| P1 | Critical path task | first scene of an act, hero shot, narration |
| P2 | Normal | ordinary shots, B-roll, ambience |
| P3 | Background | upscales, alternates, thumbnails, archive packing |

**Effective priority score** (higher runs first):

```
score = base(P) * 1000
      + critical_path_length * 25      # how many tasks wait behind this one
      + age_minutes * 2                # anti-starvation
      + (deadline_pressure ? 300 : 0)
      - (estimated_cost_credits * 0.5) # prefer cheap work when tied
      - (attempts * 40)                # repeatedly failing work yields the floor
```

**Aging rule:** no task may wait more than 45 minutes above its natural turn.
At 45 minutes it is promoted one class (P3→P2→P1). P0 is never granted by aging.

**Fairness rule:** at most 60 % of any queue's concurrency may be consumed by a
single scene, so one problem scene cannot stall the whole project.

---

## 7. SCENE DEPENDENCY GRAPH

The plan phase emits `graph/dependency_graph.json`: a DAG of tasks, plus a
second, coarser DAG of scenes.

```
BOOK
 └─ ACT
     └─ SCENE ─┬─ narration.text ──► narration.audio ──┐
               ├─ storyboard ──► shot.spec ──► shot.video ─┤
               ├─ music.plan ──────────────► music.audio ──┼─► scene.timeline ─► scene.render
               └─ ambience.plan ───────────► ambience.audio ┘
```

**Rules**
1. `narration.audio` is a dependency of `scene.timeline` for *every* scene.
   (LAW-3 — narration is the clock; you cannot lock timing without it.)
2. Shots within a scene are **siblings**, not a chain — they parallelise.
3. Scenes are siblings *unless* linked by `continuity_from`, which creates an
   edge (a scene that must match the previous scene's final frame).
4. Cross-scene character reference generation is a **shared upstream node**:
   generate the character sheet once, at P1, before any scene using it.
5. Cycle detection runs at plan time and after any graph mutation. A cycle is
   `E-SYS-205`, always fatal at plan time, never resolved automatically.

**Critical path** is recomputed whenever a task completes; the scheduler uses
`critical_path_length` from §6.

---

## 8. CHECKPOINT ENGINE

A checkpoint is a durable, resumable snapshot. Checkpoints are cheap; take them
often. Full re-runs are the most expensive failure mode in the system.

**Mandatory checkpoints**

| Checkpoint | Contains | Resume meaning |
|------------|----------|----------------|
| `CP-INGEST` | source hashes, extracted assets, OCR text | never re-OCR |
| `CP-STORY` | story graph, beats, character sheet | never re-analyse |
| `CP-PLAN` | storyboard, shot specs, prompts (versioned) | never re-plan |
| `CP-VOICE` | narration audio + timing map | never re-synthesise |
| `CP-SHOT` (per shot) | accepted video/still + QA report | never re-generate |
| `CP-SCENE` | scene timeline + scene render | never re-assemble |
| `CP-MASTER` | master render + captions | never re-render |

Checkpoint record:

```json
{ "checkpoint_id": "CP-SHOT-SH-014-03", "created_at": "…",
  "artifacts": [{ "path": "…", "sha256": "…", "bytes": 8412334 }],
  "state_snapshot_ref": "state/snapshots/2026-08-05T09-30.json",
  "inputs_fingerprint": "sha256:…",   
  "valid": true }
```

`inputs_fingerprint` = hash of (spec + references + prompt_version + model +
seed). **If the fingerprint changes, the checkpoint is invalid and the artifact
must be regenerated.** This is the entire cache-invalidation rule; nothing else
invalidates a checkpoint. Editing an unrelated scene never invalidates yours.

---

## 9. DEADLOCK & STARVATION DETECTION

**Deadlock conditions monitored every 60 s:**

| Detector | Condition | Response |
|----------|-----------|----------|
| D1 Cycle | Cycle appears in the runtime graph | `E-SYS-205`, HALT branch, human |
| D2 All-blocked | 0 tasks `READY`/`RUNNING` but > 0 `PENDING`/`BLOCKED` | diagnose blocking reason, emit report |
| D3 Approval wait | Task in `BLOCKED(awaiting_approval)` > `approval_sla` (default 24 h) | notify human, apply `on_timeout` policy |
| D4 Lease storm | Same task loses lease ≥ 3× | quarantine worker, requeue at P1 |
| D5 Starvation | Task age > 45 min above natural turn | promote priority (§6) |
| D6 Retry loop | attempts ≥ max and error class is retryable | force `FAILED`, escalate T3 |
| D7 Budget stall | All remaining tasks exceed remaining budget | HALT project, human decision |

**No auto-resolution of D1.** A cycle means the plan was wrong; a machine
guessing which edge to cut will silently break the story.

---

## 10. RETRY ENGINE

Retry is not repetition. **Every retry must change exactly one variable** and
record which. Repeating an identical call is forbidden (`E-SYS-220`).

**Retry strategy ladder** (applied in order, per artifact class):

*Visual*
1. `seed_variation` — same prompt, new seed
2. `prompt_refine` — tighten the failing axis only (M15 §11)
3. `reference_reinforce` — add/strengthen reference images
4. `motion_reduce` — lower motion complexity (most common Flow failure)
5. `shot_simplify` — reduce subjects/action; ask M17 for a shot rewrite
6. `fallback_still` — generate a still + Ken Burns instead of video

*Audio*
1. `stability_adjust` → 2. `punctuation_repunctuate` → 3. `phoneme_override`
→ 4. `segment_split` → 5. `voice_variant` (never voice *change* without approval)

*Analysis / structural*
1. `context_expand` → 2. `chunk_reduce` → 3. `model_escalate` → 4. human

**Backoff:** `wait = min(600, 5 × 2^attempt)` seconds, ±20 % jitter.

**Budget:** transient errors 3 attempts; generation errors 5; validation errors 2;
compliance errors 0. Exhaustion → `FAILED` → M12 §10 escalation.

**Model escalation rule.** Switch to a stronger/different model only when:
(a) two strategies at the current model failed, **and**
(b) the error class is `E-GEN-*` or `E-ANA-*` (not `E-INF-*`), **and**
(c) budget headroom ≥ 3× the current task's estimate.
Record the escalation in `retry_strategy_log`; never escalate silently.

**Wall-clock ceiling (distinct from the attempt-count budget above).**
Attempt-count and dollar budget (§21) bound *how many times* and *how much*,
but neither bounds *how long* a retry loop is allowed to keep sleeping and
retrying. `studio.config.json`'s `timeouts` block (same `q.*` keys as
`concurrency`) gives each queue a wall-clock ceiling in minutes;
`scripts/lib/retry.py`'s `with_retry(..., queue="q.visual")` checks
cumulative loop time (attempts + backoff, not a single call's duration)
against it on every iteration and raises `WallClockExceeded` — logged as
`E-SYS-221` — before attempts would otherwise exhaust naturally. This does
**not** interrupt a single hung call mid-flight (e.g. a subprocess with no
timeout of its own); that needs its own timeout at the call site. `queue`
is optional — omitting it keeps the old attempt-count-only behavior.

**D3's approval wait is a different clock** — not a retry loop, a human
waiting. `scripts/check_stale_human_gates.py` scans every project's
`state/approvals.jsonl` for `decision: "pending"` records older than
`human.approval_sla_hours` and reports which ones need the `on_timeout`
policy applied (advisory only — it does not itself hold/abort a project,
per §3's "you may never decide gate verdicts").

---

## 11. IDENTIFIER REGISTRY

| Object | Pattern | Example |
|--------|---------|---------|
| Project | `PRJ-<slug>` | `PRJ-taidula` |
| Act | `ACT-<nn>` | `ACT-02` |
| Scene | `SC-<nnn>` | `SC-014` |
| Shot | `SH-<scene>-<nn>` | `SH-014-03` |
| Task | `TSK-<nnnnnn>` | `TSK-000412` |
| Asset | `AST-<TYPE>-<nnnnnn>` | `AST-VID-000412` |
| Reference | `REF-<CHR\|ENV\|OBJ\|PAL>-<nnn>` | `REF-CHR-001` |
| Prompt version | `PV-<nnnn>` | `PV-0031` |
| QA report | `QAR-<nnnn>` | `QAR-0007` |
| Approval | `APR-<nnnn>` | `APR-0012` |
| Run | `RUN-<iso8601-compact>` | `RUN-20260805T0912Z` |

IDs are **immutable and never reused**, even after deletion. Counters live in
`state/id_registry.json` and are allocated by the kernel only.

---

## 12. JSON CONTRACTS

### 12.1 Envelope — every inter-agent message

```json
{
  "envelope_version": "2.0",
  "message_id": "MSG-000981",
  "run_id": "RUN-20260805T0912Z",
  "from": { "agent": "orchestrator", "version": "2.0" },
  "to":   { "agent": "visual" },
  "intent": "task.dispatch",
  "task_ref": "TSK-000412",
  "payload_schema": "flow_shot_request.schema.json",
  "payload": { },
  "idempotency_key": "TSK-000412#attempt-2",
  "created_at": "2026-08-05T09:12:00Z",
  "expects_reply": true,
  "reply_deadline_s": 900
}
```

**Contract laws**
1. Validate on send *and* on receive. Invalid → `E-CON-101`, message dropped, sender notified.
2. `idempotency_key` duplicates are ignored, not re-executed.
3. Unknown fields are preserved, never stripped (forward compatibility).
4. Version skew: minor differences tolerated; major mismatch → `E-CON-102`, HALT.
5. No prose instructions inside `payload`. Prompts live in the prompt library
   (M19) and are referenced by `PV-` id.

### 12.2 Canonical schema set (`/schemas`)

```
project.schema.json            book.schema.json           scene_index.schema.json
scene.schema.json              shot.schema.json           storyboard.schema.json
character_sheet.schema.json    style_profile.schema.json  reference_asset.schema.json
flow_shot_request.schema.json  flow_shot_result.schema.json
voice_request.schema.json      voice_result.schema.json   music_request.schema.json
timeline.schema.json           render_manifest.schema.json
asset_manifest.schema.json     dependency_graph.schema.json
task.schema.json               worker.schema.json         production_state.schema.json
qa_report.schema.json          finding.schema.json        approval.schema.json
error.schema.json              run_manifest.schema.json   cost_ledger.schema.json
```

### 12.3 `project.json` (the root contract)

```json
{
  "project_id": "PRJ-taidula",
  "title": "…",
  "bible_version": "2.0",
  "source": { "file": "input/book.pdf", "sha256": "…", "pages": 212 },
  "rights": { "source_basis": "public_domain|licensed|owned",
              "evidence_ref": "docs/rights.pdf",
              "likeness_clearance": [] },
  "output": { "aspect_ratio": "9:16", "resolution": "2160x3840", "fps": 30,
              "target_duration_s": 480, "loudness_lufs": -16 },
  "language": { "narration": "tr-TR", "captions": ["tr-TR"], "prompts": "en-US" },
  "style_profile_ref": "style/historical_epic.json",
  "audience_rating": "general",
  "budget": { "currency": "credits", "total": 5000, "alert_at": 0.8, "hard_stop_at": 1.0 },
  "determinism": { "global_seed": 20260805, "pin_models": true },
  "approval_policy": { "first_scene": "required", "master_export": "required",
                       "approval_sla_hours": 24, "on_timeout": "hold" }
}
```

**Language rule (fixes gap G-11):** `language.prompts` is the language of
generative prompts (keep English — model quality); `language.narration` and
`language.captions` are the audience-facing languages. An agent that mixes them
raises `E-CON-110`.

---

## 13. TASK DISPATCHER

```
loop every tick (2 s):
  1. refresh state from disk (single read, versioned)
  2. promote PENDING → READY where all depends_on are COMPLETED
  3. run deadlock detectors (§9) on a 60 s sub-cycle
  4. for each queue:
       capacity = concurrency_limit - running
       if backpressure(queue): capacity = 0
       candidates = READY tasks in queue, sorted by effective priority (§6)
       for task in candidates[:capacity]:
           if budget_check(task) fails: mark BLOCKED(budget); continue
           if quota_check(task) fails: leave READY; break   # do not burn the queue
           lease = assign(task, best_worker(task))
           emit envelope task.dispatch
  5. reap expired leases
  6. write state atomically, append to audit log
```

`best_worker` = capability match → lowest current load → highest recent success
rate on this task type → round-robin tie-break.

---

## 14. AGENT LIFECYCLE

```
BOOT → REGISTER → IDLE → CLAIM → LOAD_CONTEXT → EXECUTE → EMIT → SELF_CHECK → RELEASE → IDLE
                                                     │
                                                     └─ on error → REPORT → RELEASE
```

**LOAD_CONTEXT is bounded.** An agent loads: the kernel section relevant to it,
its own enterprise module, the task spec, the referenced prompt version, and at
most the last 3 QA findings on the same target. **Never the whole bible.**
Context bloat is the primary cause of instruction drift.

**SELF_CHECK before EMIT** — the agent validates its own output against the
schema and the T1 checks it can run locally. Emitting a knowingly invalid
artifact is a protocol violation, not a quality issue.

**Agent may never:** write outside its owned paths, change state directly,
approve its own output, or alter the story intent (M10 §13).

---

## 15. APPROVAL LIFECYCLE (human gate as an object)

```json
{
  "approval_id": "APR-0012",
  "scope": { "type": "scene", "target_id": "SC-001", "includes_downstream": false },
  "requested_by": "director-agent",
  "reason": "first_scene_calibration",
  "presented": { "artifacts": ["render/SC-001_preview.mp4"], "qa_report": "QAR-0007" },
  "decision": "approved_with_notes",
  "notes": "Slow the push-in on shot 2.",
  "decided_by": "producer@studio",
  "decided_at": "2026-08-05T11:04:00Z",
  "expires_at": "2026-08-12T11:04:00Z",
  "revoked": false
}
```

**Laws**
1. Approval is scoped. Approving a scene never approves the master.
2. Approval expires (default 7 days). Expired approval on an unchanged artifact
   auto-renews once; on a changed artifact it is void.
3. **Any change to an upstream input voids downstream approvals** — computed via
   `inputs_fingerprint` (§8), not by human memory.
4. `approved_with_notes` creates P1 tasks from the notes; it does not unblock
   export until those tasks complete.
5. Timeout policy from `project.approval_policy.on_timeout`:
   `hold` (default) · `proceed_p3` (continue only background work) · `abort`.
6. No agent may forge, infer, or assume approval. Absence of approval = blocked.

---

## 16. ERROR CLASSIFICATION

Code format `E-<CLASS>-<nnn>`.

| Class | Meaning | Retryable | Owner | Examples |
|-------|---------|-----------|-------|----------|
| `E-INP` | Input/source problem | rarely | Claude Code | 101 corrupt PDF, 102 unreadable scan, 103 unsupported format |
| `E-OCR` | Extraction quality | yes | Claude Code | 201 low confidence, 202 reading order broken |
| `E-ANA` | Story analysis | yes | Orchestrator | 301 no beats found, 302 chapter ambiguity |
| `E-PLN` | Planning | sometimes | AI Director | 401 shot spec incomplete, 402 duration infeasible |
| `E-GEN` | Generation | yes | Flow / ElevenLabs | 501 refusal, 502 artifact, 503 off-reference, 504 motion collapse |
| `E-SYN` | Synchronization | yes | Assembly | 601 audio drift, 602 caption overflow |
| `E-REN` | Rendering | yes | Remotion | 701 OOM, 702 codec, 703 missing asset at render |
| `E-INF` | Infrastructure | yes | Kernel | 801 timeout, 802 rate limit, 803 network, 804 quota exhausted |
| `E-CON` | Contract/protocol | no | Kernel | 101 schema invalid, 102 version skew, 110 language mismatch |
| `E-SYS` | Kernel invariant | no | Kernel | 201 illegal transition, 205 cycle, 220 identical retry, 310 queue overflow |
| `E-BUD` | Budget/cost | no | Kernel | 901 scene over cap, 902 project over cap |
| `E-LEG` | Compliance | **never** | Human | 001 rights unknown, 002 likeness, 003 age-inappropriate |

Error object:

```json
{ "error_id": "ERR-00231", "code": "E-GEN-504", "task_ref": "TSK-000412",
  "attempt": 3, "retryable": true, "message": "Motion collapse: subject deforms after frame 60",
  "evidence": { "frame": 61 }, "suggested_strategy": "motion_reduce",
  "occurred_at": "…", "worker": "WRK-visual-02" }
```

**Rate-limit rule (`E-INF-802`)**: never retry immediately, never in parallel.
Pause the whole queue, not the task.

---

## 17. HALT CONDITIONS (when production stops)

Production **HALTS** — not retries, not degrades — when any of these is true:

1. `E-LEG-*` of any kind.
2. Budget hard stop reached (`E-BUD-902`).
3. State file corruption or two writers detected.
4. Contract major version skew between agents (`E-CON-102`).
5. Cycle in the dependency graph at runtime (`E-SYS-205`).
6. QA `escape_rate` > 0.10 in the current run (systemic quality failure).
7. Source material replaced or re-hashed mid-run.
8. Three consecutive scenes requiring human review for the same axis
   (the system is mis-calibrated; continuing wastes money).

HALT writes `state/halt_report.json` with cause, affected tasks, safe-resume
point, and the exact human decision required. Only a human approval object can
clear a HALT.

**Degrade instead of halt** when: quota exhausted on one provider (switch or
queue — e.g. ElevenLabs quota exhaustion falling back to Piper per M16 §1b,
`quality_gate: "draft_only"` attached, never silently promoted to master),
one shot fails permanently (fallback to still + Ken Burns, log finding),
music generation fails (proceed with ambience only, flag in report).

A stale D3 approval wait (§9/§10) is deliberately **not** in the HALT list
above — `scripts/check_stale_human_gates.py` reports it as a finding to
review, it does not autonomously HALT a project. Escalating a stale-gate
finding to an actual HALT (e.g. under `on_timeout: "abort"`) is a human or
orchestrator decision, not this detector's.

---

## 18. PROJECT CONTEXT, MEMORY & KNOWLEDGE BASE

Three distinct stores. Confusing them is the classic failure of "AI with memory".

| Store | Lifetime | Mutable | Contents | Read by |
|-------|----------|---------|----------|---------|
| **Project Context** | one project | yes, versioned | project.json, story graph, scene specs, decisions log | all agents |
| **Memory** | one project, growing | append-only | character sheets, environment sheets, palette, voice map, prompt outcomes | agents on demand |
| **Knowledge Base** | across projects | curated by humans | templates, style profiles, prompt library, camera grammar, QA rules | all agents |

**Memory sub-types**
- *Character memory* — identity, wardrobe, face refs, voice_id, canonical phrases
- *Environment memory* — architecture, vegetation, weather, landmarks, palette
- *Style memory* — lens set, grain, color grade, motion vocabulary
- *Prompt memory* — `{prompt_version, model, seed} → {score, findings}` (this is
  what makes the system improve; it feeds M19 §6 prompt scoring)
- *Decision memory* — every M17 decision with its rationale, so later scenes can
  cite precedent instead of re-deciding

**Retrieval rule:** an agent requests memory by key, never "everything about the
project". Unbounded retrieval is the main source of context drift.

**Promotion rule:** a memory item is promoted to the Knowledge Base only after it
succeeded in ≥ 3 scenes across ≥ 2 projects, and a human approved it.

---

## 19. RESOURCE ALLOCATION & SCALING

**Tracked resources:** CPU, RAM, GPU, disk, provider quotas (Flow credits,
ElevenLabs characters, LLM tokens), concurrent API connections, render nodes.

```json
{ "resource": "flow_credits", "total": 5000, "reserved": 800, "spent": 2140,
  "reserve_policy": "reserve_on_assign", "alert_at": 0.8, "hard_stop_at": 1.0 }
```

**Reservation, not optimism.** Credits are reserved when a task is assigned and
released on completion or failure. This prevents the classic overrun where ten
parallel workers each believe the full budget is available.

**Scaling ladder**
1. *Vertical* — raise per-queue concurrency until backpressure appears.
2. *Horizontal (local)* — more workers per role on the same machine.
3. *Cloud workers* — stateless role containers pulling from the same queue.
4. *Distributed render* — see §19.2.

**19.1 Parallel production rules**
- Scenes parallelise freely; shots within a scene parallelise freely.
- Narration for a scene is generated **before** its shots (clock first).
- Character/reference generation is serialised and global (§7 rule 4).
- Max parallel scenes = `min(quota_headroom / avg_scene_cost, 60% rule from §6)`.
- Two scenes linked by `continuity_from` never run in parallel.

**19.2 Distributed rendering**
- Split unit = **scene**, never arbitrary frame ranges (audio continuity).
- Each node receives: scene timeline, its assets, deterministic seed, font pack.
- Node output: `SC-nnn.mov` (intermediate codec, ProRes or DNxHR) + hash.
- Concatenation is a separate P1 task; re-encode once at the end, never twice.
- Fonts, LUTs and codec versions must be pinned per node — mismatch is the
  number-one cause of invisible drift across a distributed render.
- Node failure → scene requeued whole; partial frames are discarded, never merged.

---

## 20. OBSERVABILITY

**Every task emits** (append-only, `logs/events.ndjson`):
`ts, run_id, task_id, type, state_from, state_to, worker, duration_ms, cost, error_code, qa_score`

**Run report** (`reports/run_<run_id>.md`) is generated at every terminal state
and contains: timeline of states, cost breakdown by queue, first-pass yield,
retry histogram by strategy, top 10 slowest tasks, all findings by severity,
human touches, and a diff against the previous run of the same project.

**System SLOs**
| Metric | Target |
|--------|--------|
| Task dispatch latency | p95 < 5 s |
| Lease loss rate | < 1 % |
| First-pass yield | ≥ 0.65 |
| Cost variance vs estimate | ±20 % |
| Resume-after-crash success | 100 % |
| Human touch rate | ≤ 8 % of artifacts |

---

## 21. COST GOVERNANCE

`state/cost_ledger.json` — append-only, one row per API call:

```json
{ "ts": "…", "task_id": "TSK-000412", "provider": "flow", "operation": "video_gen",
  "units": 1, "unit_cost": 30, "cost": 30, "attempt": 2, "accepted": false }
```

**Rules**
1. Every task has an estimate before dispatch; missing estimate = not dispatchable.
2. Scene-level cap = `1.5 × scene_estimate`. Breach → `E-BUD-901`, scene blocked,
   human decides: approve overage / simplify shots / drop to stills.
3. Rejected generations still cost money — they are recorded with
   `accepted: false`, and `waste_ratio = wasted_cost / total_cost` is reported.
   `waste_ratio > 0.35` is an alarm: the prompts are wrong, not the model.
4. Alert at 80 % of project budget; HALT at 100 %.

---

## 22. DETERMINISM & REPRODUCIBILITY

`run_manifest.json` records, for the entire run: bible version, module versions,
schema versions, model ids and versions, global seed and per-task seeds, prompt
versions, reference asset hashes, font/LUT versions, and the container image.

**Replay contract**
- *Deterministic artifacts* (timelines, captions, manifests, renders from fixed
  inputs) must be byte-identical.
- *Generative artifacts* must be perceptually equivalent: same seed + same model
  + same prompt version. If the provider changed the model behind the version
  string, mark the run `replay_broken: true` and record it — never pretend.

---

## 23. AUTOMATIC vs HUMAN REVIEW BOUNDARY

| Decision | Machine may decide | Human required |
|----------|-------------------|----------------|
| Technical pass/fail | ✅ | — |
| Retry strategy selection | ✅ | — |
| Continuity conformance | ✅ | if drift is intentional |
| Shot rewrite (small) | ✅ via M17 | — |
| Story change | ❌ | ✅ always |
| Voice identity change | ❌ | ✅ always |
| Rights / likeness | ❌ | ✅ always |
| Budget overage | ❌ | ✅ always |
| Final export | machine prepares | ✅ approves |

---

## 24. OUTPUT CONTRACT

```
state/production_state.json    state/id_registry.json     state/cost_ledger.json
state/snapshots/*.json         state/halt_report.json
graph/dependency_graph.json    queue/queue_status.json    worker/worker_status.json
logs/events.ndjson             logs/audit_log.ndjson
reports/run_<run_id>.md        run_manifest.json
```

## 25. FAILURE MODES OF THE OS ITSELF

| Mode | Symptom | Fix |
|------|---------|-----|
| Zombie worker | lease held, no heartbeat | lease reaping (§5) |
| Thundering herd | all workers retry a rate-limited API at once | queue-level pause + jitter |
| Priority inversion | P3 upscales block P1 shots on the same quota | per-class quota reservation |
| Checkpoint rot | fingerprint not recorded, stale artifact reused | fingerprint mandatory (§8) |
| Approval drift | human approved v1, system exported v3 | fingerprint-based voiding (§15.3) |
| State split-brain | two writers | kernel-only writes, atomic rename, PID lock |

## 26. ACCEPTANCE CRITERIA

- A crash at any point resumes with zero re-generation of accepted artifacts.
- Every artifact traces to a task, a prompt version, a seed and a QA report.
- No message crosses agents without schema validation.
- Cost never exceeds `hard_stop` without a human approval object.
- Every HALT produces an actionable report naming the single required decision.

**NEXT MODULE:** Module 14 — Claude Code Enterprise

**CHANGELOG**
- v2.0 — Full kernel rewrite: leases, budgets, deadlock detection, determinism,
  approval objects, error codes, HALT semantics, distributed render rules.
- v1.0 — Initial outline.

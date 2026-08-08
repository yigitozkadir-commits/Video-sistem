# MODULE 20 — AI AUDIOBOOK STUDIO OS v1
**Version 2.0 · Layer 8 (Runtime) · The binding module**

> Modules 1–19 describe parts. This module is the machine: what runs, in what
> order, with what commands, and what "done" means.

**Naming note (added 2026-08-07):** "v1" in this module's title is the
*product's* version (the first shippable end-to-end pipeline), unrelated to
"Version 2.0" in the line above, which is this *document's* own revision
number (same versioning scheme every bible module uses). The two numbers
answering different questions is confusing on first read - noted here rather
than renamed, since "v1" is also how every real project's output has
actually been described in commit messages and manifests so far.

**Relationship to M13 (added 2026-08-07):** M13 is Layer 4, the kernel -
it specifies rules (state machine, task/worker/queue objects, halt
conditions) that would govern the system *if* it ran as a multi-agent OS.
M20 is Layer 8, the runtime - it's the concrete, currently-true binding of
modules 1-19 into the pipeline that has actually produced every finished
video so far. Where M13 describes the not-yet-built queue/worker apparatus,
M20 is what really runs: one task at a time, driven by direct user requests,
with checkpoints and manifests instead of a task queue. Read M20 for "what
actually happens"; read M13 for "what a scaled-up version of this would
need."

---

## 1. SYSTEM DEFINITION

**AI Audiobook Studio OS v1** = a deterministic, resumable, budget-governed
pipeline that converts one source book into one finished cinematic audiobook
video, with recorded reasons for every creative choice.

**Inputs:** a source file + `project.json` + a template id.
**Output:** a master video, stems, captions, manifests, and a run report that
makes the whole production auditable and repeatable.

---

## 2. REPOSITORY LAYOUT

```
studio/
├─ bible/                 Modules 01–20 (specs, this document set)
├─ schemas/               JSON Schema Draft 2020-12 (M13 §12.2)
├─ prompts/               PV-* prompt objects + axes (M19)
├─ templates/             TPL-* (M18) + style/*.json
├─ kernel/                scheduler, queues, state, checkpoints, cost ledger
├─ agents/                orchestrator · technical · visual · audio · review · director
├─ adapters/              flow/ · elevenlabs/ · llm/ · remotion/ · ffmpeg/
├─ knowledge/             cross-project curated memory (M13 §18)
└─ projects/
   └─ PRJ-<slug>/
      ├─ input/           immutable source
      ├─ extracted/ ocr/  M14 output
      ├─ beats/ scenes/   story + shot specs
      ├─ decisions/       DEC-* (M17)
      ├─ prompts_used/    resolved prompt instances per task
      ├─ assets/          video/ image/ audio/ reference/
      ├─ timeline/ render/
      ├─ qa/ reports/ logs/ state/ graph/
      └─ output/          master + delivery package
```

**Adapters exist so providers are replaceable (M01 §9).** No agent may call a
provider SDK directly; it calls the adapter interface. Swapping Flow for another
video model must touch only `adapters/flow/`.

---

## 3. ADAPTER INTERFACE (provider independence)

```ts
interface VisualAdapter {
  generateShot(req: FlowShotRequest): Promise<ShotResult>   // returns candidates + cost + model_version
  generateStill(req: StillRequest): Promise<StillResult>
  upscale(req: UpscaleRequest): Promise<StillResult>
  capabilities(): { maxDurationS: number; aspectRatios: string[]; supportsReferences: boolean }
}
interface AudioAdapter  { synthesize(); music(); ambience(); timingMap(); }
interface RenderAdapter { compose(); render(); probe(); }
```

Every adapter must report `model_version` and `cost` on every call, or the
determinism (M13 §22) and cost (M13 §21) laws cannot hold.

---

## 4. BOOT SEQUENCE

```
1. Load bible version + schema registry        → fail fast on version skew (E-CON-102)
2. Validate project.json                       → E-CON-101 on failure
3. Resolve template + style profile            → conflict check (E-PLN-402)
4. Verify rights basis                         → unknown = HALT (E-LEG-001)
5. Check provider credentials + quota headroom → E-INF-804
6. Reserve budget, open cost ledger
7. Restore last checkpoint if a run exists     → else create RUN-<ts>
8. Build/validate dependency graph             → cycle = fatal (E-SYS-205)
9. Register workers, start dispatcher
10. Emit run_manifest.json
```

Boot never starts generation. Generation begins only after PLAN passes its gate.

---

## 5. THE RUN LIFECYCLE (end to end)

| Phase | What happens | Gate | Human? |
|-------|--------------|------|--------|
| 1. Ingest | M14: extraction, OCR, image catalog + dispositions | all inputs cataloged | on `HOLD_LEGAL` |
| 2. Analyse | Orchestrator: chapters → scenes → beats (M17 §4) | beat map complete | no |
| 3. Direct | M17: shot design, camera, still/video, music, silence | storyboard gate | **first scene: yes** |
| 4. Voice | M16: narration per beat + timing map | audio T1+T2 | no |
| 5. Reference | M15: character/environment sheets, locked | identity gate | **yes (lock)** |
| 6. Generate | M15: shots and stills, scene by scene | shot_accept | on plateau/legal |
| 7. Score & ambience | M16: music cues, ambience, SFX | audio gate | no |
| 8. Assemble | M14+M11: timeline, captions, scene renders | scene_accept | no |
| 9. Master | Remotion: full render, mix, normalise | master_export | **yes** |
| 10. QA & report | M12 full sweep, run report, archive | reproducibility check | no |

**Order law:** voice before visuals, always (LAW-3). References before any scene
using them. Nothing generative before the storyboard gate.

---

## 6. COMMAND SURFACE

```bash
studio init      --source book.pdf --template TPL-historical-epic --aspect 9:16
studio ingest                          # phase 1
studio analyse                         # phase 2
studio direct    --act 1               # phase 3, writes decisions/
studio voice     --scene SC-014        # phase 4
studio refs      --lock                # phase 5
studio generate  --scene SC-014        # phase 6 (respects budget + gates)
studio assemble  --scene SC-014
studio master
studio status                          # state, queues, budget, blockers
studio why       SH-014-03             # M17 interrogation mode
studio approve   --scope scene --id SC-001 --decision approved_with_notes --note "…"
studio resume                          # from last checkpoint
studio halt / studio abort
studio report    --run RUN-20260805T0912Z
studio replay    --run RUN-… --verify  # determinism check
```

`studio why` is not a convenience — it is the acceptance test for the whole
system. If it cannot answer, the production was undirected.

---

## 7. RUNTIME CONFIG (`studio.config.json`)

```json
{
  "bible_version": "2.0",
  "concurrency": { "q.visual": 3, "q.voice": 3, "q.render": 2, "q.qa": 6 },
  "providers": { "visual": "flow", "audio": "elevenlabs", "llm_plan": "…", "llm_review": "…" },
  "budget": { "alert_at": 0.8, "hard_stop_at": 1.0 },
  "human": { "approval_sla_hours": 24, "on_timeout": "hold",
             "notify": ["producer@studio"] },
  "determinism": { "pin_models": true, "record_seeds": true },
  "safety": { "block_on_legal_findings": true, "children_mode_auto": true }
}
```

---

## 8. THE THREE LOOPS

The system improves through three nested loops. Most AI pipelines have only the
first and therefore never get better.

**Loop 1 — Task loop (seconds to minutes).** generate → QA → retry with one
changed variable → accept. Improves a single artifact.

**Loop 2 — Scene loop (per scene).** Director reviews its own decisions against
QA outcomes (M17 §14), adjusts precedent, updates prompt stats (M19 §6).
Improves the rest of *this* project.

**Loop 3 — Studio loop (per project).** Run report → prompt promotions/retirements
→ template refinements → memory promoted to Knowledge Base after 3 projects.
Improves *every future* project.

---

## 9. WHAT "DONE" MEANS

A project is `COMPLETE` when **all** hold:

1. Master render passes `master_export` gate (M12 §5).
2. Every artifact traces to task → prompt version → seed → QA report → decision.
3. No open `LEG` findings; rights basis recorded.
4. Delivery package complete (§10).
5. `studio replay --verify` reproduces deterministic artifacts byte-identically.
6. Run report generated and archived.
7. A human approval object exists for the master.

Anything less is `EXPORTED_PROVISIONAL`, and must be labelled as such.

---

## 10. DELIVERY PACKAGE

```
output/
├─ master.mp4                  H.264, target aspect, −16 LUFS
├─ master_archive.mov          ProRes/DNxHR
├─ audio/                      narration, dialogue, music, ambience, sfx stems + mix
├─ captions.srt / captions.ass
├─ thumbnail.png / keyframes/
├─ manifests/                  asset · scene · render · run · cost
├─ qa/                         reports, findings, continuity
├─ decisions/                  the full directorial record
└─ README.md                   how this was made, how to reproduce it
```

---

## 11. FAILURE PLAYBOOK (operator quick reference)

| Situation | First move |
|-----------|-----------|
| Everything blocked, nothing running | `studio status` → D2 detector output → find the blocking dependency |
| Budget alarm at 80 % | Check `waste_ratio` per scene; if > 0.35 fix prompts before buying attempts |
| Shot fails 3× | Stop retrying — `fallback_still`, log finding, move on; revisit at act close |
| Faces drift across a scene | Re-lock reference, regenerate from the scene anchor, not from scratch |
| Audio/video drift over a long render | Re-derive frames from the timing map; never nudge by hand |
| Model refusal | Read the refusal; if the content is genuinely disallowed, escalate — never rephrase to evade |
| HALT | Read `halt_report.json`; it names the single decision required |

---

## 12. ROADMAP BEYOND v1

- **v1.1** — multi-language narration from one plan (captions + dubbing stems)
- **v1.2** — distributed render farm with node pinning (M13 §19.2 hardening)
- **v1.3** — episodic memory across a book series (shared character canon)
- **v1.4** — learned prompt selection: pick `PV-` by predicted score, not by rule
- **v1.5** — interactive review UI: scrub, comment, and emit approval objects
- **v2.0** — branching narratives and per-viewer adaptive length

Each requires the same discipline: no feature ships without a schema, a gate, and
an acceptance criterion.

---

## 13. SYSTEM ACCEPTANCE CRITERIA

- A cold crash at any second resumes with zero re-generation of accepted work.
- `studio why <artifact>` answers from the log for 100 % of artifacts.
- Cost never exceeds hard stop without an approval object.
- Replay verification passes.
- A second operator, given only the repository, can reproduce the film.

**CHANGELOG**
- v2.0 — Module created: repository layout, adapter contracts, boot sequence, run
  lifecycle, command surface, three improvement loops, done-definition, roadmap.

---

### END OF PRODUCTION BIBLE v2.0
Modules 01–11 remain at v1.0 (doctrine and tool guides) and should be re-issued
in v2.1 with Output Contract / Failure Modes / Acceptance Criteria sections to
match the v2.0 house format.

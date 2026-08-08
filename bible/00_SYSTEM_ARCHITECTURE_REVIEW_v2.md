# AI AUDIOBOOK PRODUCTION BIBLE
## SYSTEM ARCHITECTURE REVIEW — v1.0 → v2.0 (OS Upgrade)

**Reviewed:** Modules 01–11, 13–16 (v1.0, 43 KB total)
**Verdict:** Solid *taxonomy*, no *executable semantics*. This document lists what
is missing and defines the v2.0 rules that Modules 12–20 implement.

---

## 1. WHAT v1.0 GOT RIGHT

- Clear agent separation (Orchestrator / Technical / Visual / Audio).
- JSON-between-stages principle, no hidden state.
- Immutable input, versioned artifacts, append-only logs.
- Scene as the atomic production unit.
- Narration as the master clock (M11 §7) — this is the single most
  important timing decision in the whole system. Keep it forever.

## 2. STRUCTURAL GAPS FOUND

| # | Gap | Impact | Fixed in |
|---|-----|--------|----------|
| G-01 | **Module 12 missing entirely.** M11 hands off to "Module 12 – AI Quality Assurance Bible" which does not exist. QA is referenced by 9 other modules. | Broken chain | **Module 12** |
| G-02 | Modules are *bullet lists*, not *contracts*. "Score 0–100" with no rubric, no threshold, no tie-break. An AI cannot execute a taxonomy. | Non-deterministic output | 12–20 |
| G-03 | No machine-readable schema anywhere. `project.json` is named in M02 but never defined. | No validation possible | **M13 §12** |
| G-04 | No global ID / namespace registry. M09 shows `AST-IMG-000123` as an example only. | Collisions, broken links | **M13 §11** |
| G-05 | No error taxonomy with codes. M13 v1.0 lists 7 "error classes" with no codes, no retryability flag, no owner. | Retry loops, silent failure | **M13 §16** |
| G-06 | No cost / quota governance. Whole system is API-metered; no budget, no kill-switch. | Runaway spend | **M13 §21** |
| G-07 | No determinism spec: seeds, model version pinning, temperature. M01 promises "reproducible" but nothing enforces it. | Not reproducible | **M13 §22** |
| G-08 | Human approval mentioned but never modelled: who, scope, expiry, revocation. | Ungoverned gates | **M13 §15** |
| G-09 | No deadlock / starvation handling in the dependency graph. | Silent hang | **M13 §9** |
| G-10 | Role conflict: M02 gives the Orchestrator to ChatGPT; M14 makes Claude Code a "Production Director"; M17 introduces an AI Director. Three deciders, no precedence rule. | Contradictory decisions | **M17 §2 (Authority Ladder)** |
| G-11 | No language/locale model. Narration language ≠ prompt language ≠ subtitle language. | Wrong-language renders | **M16 §3**, M13 §12 |
| G-12 | No aspect-ratio strategy. 9:16 vertical and 16:9 need different shot grammar. | Reframing loss | **M17 §11**, M18 |
| G-13 | Rights / licensing layer absent: source-book copyright, voice licensing, model ToS, likeness of real people. | Legal exposure | **M12 §11** |
| G-14 | Prompts are prose, not versioned testable objects. | Undebuggable quality | **M19 §2** |
| G-15 | No observability: no metrics, no SLO, no run report. | Cannot improve | **M13 §20** |
| G-16 | No "stop" semantics. Nothing in v1.0 ever halts production. | Bad output ships | **M13 §17 HALT** |

## 3. v2.0 CORE LAWS (bind every module)

1. **LAW-1 — Contract over prose.** Every inter-agent message validates against a
   schema in `/schemas`. Unvalidated message = dropped message.
2. **LAW-2 — Single Writer.** Exactly one agent may write a given artifact path.
   Everyone else reads. Ownership table: M13 §5.
3. **LAW-3 — Narration is the clock.** Visual duration bends to audio, never the
   reverse. Only the AI Director (M17) may request a narration re-cut.
4. **LAW-4 — No silent degradation.** Any quality drop must emit a `qa_finding`
   with severity. A pass with unrecorded compromise is a system failure.
5. **LAW-5 — Deterministic replay.** Given `project.json` + `run_manifest.json`,
   a rerun must produce byte-identical deterministic artifacts and
   perceptually-equivalent generative artifacts (seed + model pinned).
6. **LAW-6 — Cost is a first-class constraint.** Every task carries an estimated
   and actual cost. Budget exhaustion is a HALT condition, not a warning.
7. **LAW-7 — Human gate is explicit.** Human approval is an object with scope and
   expiry, never an assumption.
8. **LAW-8 — Fail loud, resume cheap.** Failure stops the smallest possible unit
   (a shot, not a project) and resumes from the last checkpoint.

## 4. MODULE MAP AFTER UPGRADE

```
LAYER 0  DOCTRINE      M01 Foundation · M02 Agent Architecture
LAYER 1  TOOL GUIDES   M03 Claude · M04 Orchestrator · M05 Story
                       M06 Flow · M07 ElevenLabs · M08 Prompting
LAYER 2  DATA          M09 Assets · M10 Scenes · M11 Remotion
LAYER 3  GOVERNANCE    M12 QA Bible            ← NEW (was missing)
LAYER 4  KERNEL        M13 Production OS       ← rewritten
LAYER 5  ENTERPRISE    M14 Claude Code · M15 Flow · M16 ElevenLabs
LAYER 6  INTELLIGENCE  M17 AI Director         ← the heart
LAYER 7  APPLICATION   M18 Templates · M19 Prompt Library
LAYER 8  RUNTIME       M20 Studio OS v1        ← binds everything
```

**Dependency rule:** a module may only depend downward (higher layer → lower
layer). M17 may call M13; M13 may never call M17.

## 5. NAMING & FILE CONVENTIONS (v2.0)

- Specs: `Module_NN_Name.md` — Markdown, English (schemas and prompts must stay
  English; runtime *content* language is set per project in `project.json`).
- Schemas: `/schemas/<object>.schema.json`, JSON Schema Draft 2020-12.
- Every module ends with: Output Contract · Failure Modes · Acceptance Criteria ·
  Changelog. A module without acceptance criteria is a draft, not a spec.

## 6. READING ORDER FOR AN AI AGENT

`M13 (kernel)` → `M12 (quality law)` → `M17 (decision authority)` → the
enterprise module for its own role (M14/M15/M16) → `M19` for prompt bodies.
Never load all modules; load the kernel plus your role.

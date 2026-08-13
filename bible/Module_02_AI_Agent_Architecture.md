# MODULE 02 — AI AGENT ARCHITECTURE
**Version 2.1 · Layer 0 (Doctrine)**

## 1. MISSION

Define every agent, what it may decide, what it owns, and how it speaks.

**Rule of the module:** an agent is defined by its *authority boundary*, not by
its tool. "Claude does OCR" is a capability. "Claude may decide extraction method
but not story meaning" is an architecture.

## 2. AGENT ROSTER

| Agent | Implementation | May decide | May never decide |
|-------|---------------|------------|------------------|
| **Kernel** | code | scheduling, leases, budget, halt | anything creative |
| **Orchestrator** | LLM (M04) | script, beat segmentation, sequencing, prompt assembly | shot design, final gates |
| **AI Director** | LLM (M17) | scenes, shots, rhythm, music, silence, cuts | story events, rights, budget |
| **Technical** | Claude Code (M14) | extraction, classification, manifests, timelines | story, prompts, aesthetics |
| **Visual** | Flow (M15) | prompt realisation, seeds, retries within ladder | what the shot is |
| **Audio** | ElevenLabs (M16) | delivery, pauses, mix, pronunciation | the words, voice identity |
| **Review** | LLM+vision (M12) | scores, findings, gate verdicts | fixes, creative changes |
| **Human** | person | story, rights, budget, exports, locks | — |

**Generator ≠ reviewer.** No agent may review its own output (M12 §7.5).

## 3. COMMUNICATION

All traffic is an envelope (`envelope.schema.json`, M13 §12.1). Rules:

1. Validate on send and on receive.
2. Idempotency key duplicates are ignored, never re-executed.
3. Unknown fields are preserved, never stripped.
4. No free prose instructions in a payload — reference a `PV-` prompt instead.
5. No side channels. If it isn't in an envelope or a file, it didn't happen.

## 4. HANDOFF CONTRACT

| From → To | Artifact | Gate before handoff |
|-----------|----------|---------------------|
| Technical → Orchestrator | `book.json`, `image_catalog.json`, `scene_candidates.json` | OCR confidence |
| Orchestrator → Director | `beat_map.json`, script | beat validity |
| Director → Visual | `shot_plan.json` + references | storyboard gate |
| Director → Audio | `voice_script`, `music_plan.json` | — |
| Audio → Technical | `timing_map.json` | audio T1+T2 |
| Visual+Audio → Technical | accepted assets | shot_accept |
| Technical → Review | `timeline.json`, renders | preflight |
| Review → Human | QA report + approval request | trigger list (M12 §10) |

**No downstream agent may change story intent** (M10 §13). A downstream agent
that believes the intent is wrong raises a finding; it does not act.

## 5. AGENT LIFECYCLE

`BOOT → REGISTER → IDLE → CLAIM → LOAD_CONTEXT → EXECUTE → EMIT → SELF_CHECK → RELEASE`

**LOAD_CONTEXT is bounded** and this is not optional: kernel section for its role,
its own enterprise module, the task spec, the referenced prompt, and at most the
last 3 findings on the same target. Loading the whole bible is the primary cause
of instruction drift and is a defect.

**SELF_CHECK** — the agent validates its own output against the schema and the
local T1 checks before emitting. Emitting a knowingly invalid artifact is a
protocol violation, not a quality issue.

## 6. STATE

Agents are stateless between tasks. All continuity lives in files:
project context, memory, knowledge base (M13 §18). An agent that relies on
conversational memory cannot be resumed, parallelised, or audited.

## 7. FAILURE POLICY

- Transient → retry with backoff (M13 §10), attempt count incremented.
- Infrastructure loss (lease expiry) → requeue, attempt count **not** incremented.
- Contract violation → no retry; fix the sender.
- Compliance → no retry; human.
- Never overwrite a successful artifact. Never resume mid-task; resume from
  checkpoint.

## 8. DIRECTORY OWNERSHIP (LAW-2)

`input/` nobody · `extracted/ ocr/` technical · `beats/ scenes/` orchestrator+director ·
`decisions/` director · `assets/video|image/` visual · `assets/audio/` audio ·
`timeline/ render/` technical · `qa/` review · `state/ logs/` kernel.

## 9. OUTPUT CONTRACT

```
agents/<role>/manifest.json     capabilities, owned paths, schemas consumed/produced
worker/worker_status.json       runtime registration (M13 §5)
```

## 10. FAILURE MODES

| Mode | Symptom | Fix |
|------|---------|-----|
| Role creep | Visual agent starts rewriting shots | Authority table + rejected-alternatives audit |
| Side channel | Decision made in chat, not in a file | Envelope-only rule; unlogged = void |
| Context bloat | Agent loads everything, drifts | Bounded LOAD_CONTEXT |
| Self-review | Generator scores itself 95 | Generator ≠ reviewer enforced by kernel |

## 11. ACCEPTANCE CRITERIA

- Every agent has a written authority boundary and an owned path set.
- 100% of inter-agent traffic is schema-valid.
- No artifact exists whose creator cannot be identified.

**NEXT:** Module 03 — Claude Code Master Guide

**CHANGELOG** v2.1 — Authority boundaries, handoff gates, bounded context, ownership.

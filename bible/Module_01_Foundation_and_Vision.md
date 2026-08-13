# MODULE 01 — FOUNDATION & VISION
**Version 2.1 · Layer 0 (Doctrine) · Status: NORMATIVE**

## 1. PURPOSE

A reusable, provider-agnostic production system that converts a book into a
cinematic audiobook video — with recorded reasons for every creative choice and
the ability to reproduce the result from the repository alone.

**Not a goal:** maximum automation. The goal is *maximum accountable automation*.
A pipeline that produces beautiful footage nobody can explain or reproduce has
failed this bible.

## 2. THE EIGHT LAWS

These bind every module. A module may add constraints, never remove one.

| Law | Statement | Enforced by |
|-----|-----------|-------------|
| LAW-1 | Contract over prose. Every inter-agent message validates against a schema. | M13 §12 |
| LAW-2 | Single Writer. One agent owns each artifact path. | M13 §5 |
| LAW-3 | Narration is the clock. Visual timing bends to audio, never the reverse. | M16, M11 |
| LAW-4 | No silent degradation. Every quality compromise emits a finding. | M12 |
| LAW-5 | Deterministic replay. Seed + model + prompt version recorded always. | M13 §22 |
| LAW-6 | Cost is a constraint, not a report. Budget exhaustion halts. | M13 §21 |
| LAW-7 | Human gates are explicit objects with scope and expiry. | M13 §15 |
| LAW-8 | Fail loud, resume cheap. Stop the smallest unit; resume from checkpoint. | M13 §8 |

## 3. DESIGN PRINCIPLES

- **Modular** — each module is replaceable without touching the others.
- **Provider-agnostic** — providers live behind adapters (M20 §3). Swapping the
  video model must touch one directory.
- **AI-first, human-gated** — machines decide within bounds; humans decide the
  bounds and the exits.
- **Single Source of Truth** — `project.json` for intent, `production_state.json`
  for runtime. Anything an agent "remembers" is advisory and expires.
- **Reproducible** — the repository, not a person's memory, is the studio.
- **Auditable** — `studio why <artifact>` must answer from the log.

## 4. PIPELINE OVERVIEW

```
Source → Ingest → Analyse → Direct → Voice → References → Generate
       → Score/Ambience → Assemble → Master → QA → Archive
```

**Order law:** voice before visuals (LAW-3); references before any scene that
uses them; nothing generative before the storyboard gate.

## 5. THE FIVE ROLES

| Role | Module | Owns |
|------|--------|------|
| Kernel | M13 | state, scheduling, budget, halt |
| Orchestrator | M04 | script, beats, sequencing, dispatch proposals |
| AI Director | M17 | creative decisions and their reasons |
| Enterprise agents | M14/M15/M16 | technical, visual, audio execution |
| Review agent | M12 | scoring, findings, gate verdicts |

Authority precedence is defined once, in M17 §2. No other module may restate it.

## 6. DIRECTORY STANDARD

See M20 §2 for the full repository. Per project:

```
input/ extracted/ ocr/ beats/ scenes/ decisions/ prompts_used/
assets/{video,image,audio,reference}/ timeline/ render/
qa/ reports/ logs/ state/ graph/ output/
```

`input/` is immutable after ingest. `logs/` is append-only. `state/` is written
by the kernel only.

## 7. THE SCENE PACKAGE

A scene is the smallest independently producible narrative unit and carries:

```
scene.json · beats.json · storyboard.json · shots/*.json
narration/*.wav + timing_map.json · music_plan.json
timeline.json · decisions/*.json · qa/*.json
```

A scene missing any of these is not producible; it is a draft.

## 8. QUALITY STANDARD

Defined numerically in M12. In prose: narrative clarity, visual consistency,
audio synchronisation, caption accuracy, music balance, deliberate rhythm.
None of these are opinions in this system — each maps to a scored axis.

## 9. VERSIONING

- **Bible:** major = law or contract change; minor = new capability; patch = fix.
- **Artifacts:** never overwritten; a new version is a new file and a new id.
- **Schemas:** additive changes are minor; a removed or retyped field is major
  and triggers `E-CON-102` against older agents.

## 10. DEVELOPMENT RULES

1. No provider SDK called outside `adapters/`.
2. No prompt text inside code or module prose — prompts live in M19 as objects.
3. Every new feature ships with a schema, a gate, and an acceptance criterion.
4. Every module ends with Output Contract, Failure Modes, Acceptance Criteria.
5. Nothing is "temporary". Temporary code becomes permanent undocumented law.

## 11. OUTPUT CONTRACT

```
project.json            the intent of one production
studio.config.json      runtime configuration
bible/                  these modules, versioned together
```

## 12. FAILURE MODES

| Mode | Symptom | Fix |
|------|---------|-----|
| Doctrine drift | Modules contradict each other | Laws restated in exactly one place |
| Tool worship | Bible describes tools, not decisions | Every guide module must state what it *decides* |
| Silent defaults | Production runs without a template | M18 §7: no project runs on defaults |

## 13. ACCEPTANCE CRITERIA

- Every module in the bible declares its layer, authority and limits.
- The eight laws appear in exactly one normative place (here) and are referenced,
  never re-argued, elsewhere.
- A new engineer can locate the owner of any artifact path in under a minute.

**NEXT:** Module 02 — AI Agent Architecture

**CHANGELOG** v2.1 — Eight laws, role table, order law, house format.

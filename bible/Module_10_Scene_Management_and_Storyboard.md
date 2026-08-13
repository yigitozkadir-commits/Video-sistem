# MODULE 10 — SCENE MANAGEMENT & STORYBOARD SYSTEM
**Version 2.1 · Layer 2 (Data)**

## 1. SCENE PHILOSOPHY

A scene is the smallest independently producible narrative unit. It must have one
primary purpose, one dominant emotion, be comprehensible in isolation, and carry
all of its production metadata.

## 2. LIFECYCLE

`Candidates (M14) → Boundary approval (M17) → Beats (M04) → Storyboard (M17)
→ Narration (M16) → Shot generation (M15) → Timeline (M14) → QA (M12)`

Scene boundaries are **proposed by the technical agent and approved by the
Director**. This split matters: detection is mechanical, meaning is not.

## 3. LENGTH CONSTRAINTS

Target 20–90 s. Over 120 s → split at the strongest internal signal. Under 8 s →
merge. Every adjustment is recorded as a finding, so the Director can override.

## 4. DATA MODEL

See `scene.schema.json`. Mandatory: `scene_id, title, summary`. Production-ready
also requires: duration estimate, emotion, characters, location, shots, and a
`continuity_from` value (possibly null).

## 5. STORYBOARD

A storyboard is an ordered list of shot specs (`shot.schema.json`). Every shot
carries camera, lens, framing, motion level, duration, references, prompt
version, seed and a `decision_ref`. **A shot without a decision reference was
produced without direction** and fails M17 §15.

## 6. SHOT RHYTHM FLOOR

Across any five consecutive shots: at most two moving shots, at least one
close-up, at least one wide, and no three consecutive identical durations
(±0.2 s). This is legibility, not style; templates may tighten it (M18).

## 7. DURATION

Derived, never chosen: narration duration (M16 timing map) + designed silence +
comprehension margin (M17 §5). Rounded to frames once, at the timeline boundary
(M14 §10).

## 8. CONTINUITY

`continuity_from` creates a hard edge in the dependency graph: the referenced
scene must complete first, and its final frame becomes a reference for the first
shot of this scene. Two scenes linked this way never run in parallel.

## 9. OUTPUT CONTRACT

```
scenes/scene_index.json · scenes/SC-*/scene.json · storyboard.json
shots/*.json · camera_plan.json · asset_requests.json · timeline.json
```

## 10. FAILURE MODES

| Mode | Symptom | Fix |
|------|---------|-----|
| Scene explosion | 400 candidates | Length constraints before emitting |
| Undirected shots | No decision_ref | Reject at storyboard gate |
| Machine-gun pacing | Every shot 4.0 s | Rhythm floor check |
| Continuity break | Scene 15 contradicts 14 | continuity_from edge + anchor frame |

## 11. ACCEPTANCE CRITERIA

- Every scene falls within length constraints or carries a rationale.
- Every shot has a decision reference and a prompt version.
- Rhythm floor satisfied per act, reported in `rhythm_report.json`.

**NEXT:** Module 11 — Remotion Production Pipeline

**CHANGELOG** v2.1 — Proposal/approval split, rhythm floor, derived duration, continuity edges.

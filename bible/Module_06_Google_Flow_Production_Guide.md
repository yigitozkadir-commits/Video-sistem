# MODULE 06 — GOOGLE FLOW PRODUCTION GUIDE
**Version 2.1 · Layer 1 (Tool Guide) · Deep spec: M15**

## 1. ROLE

Practical operation of Flow. The DSL, consistency system and retry ladder live in
M15; this module is the operator's baseline.

## 2. WHAT FLOW IS GOOD AT / BAD AT

| Reliable | Unreliable |
|----------|-----------|
| Single subject, simple motion | Crowds, combat, complex physics |
| Atmospheric environment motion | Text and signage |
| Slow camera moves | Fast tracking with turns |
| Portrait framing at motion 1–2 | Close-up faces at motion ≥ 3 |
| Consistent look with references | Consistency across many references |

**Design to the reliable column.** Most "Flow is bad" problems are shot design
problems, not model problems.

## 3. THE 9-SLOT PROMPT

`SUBJECT · ACTION · ENVIRONMENT · LIGHTING · CAMERA · LENS · MOTION · STYLE ·
TECHNICAL` + a negative base. Identity goes first: early tokens carry more
weight. Full spec: M15 §3.

## 4. MOTION BUDGET

One primary motion per shot. Camera move + subject action + environment motion
simultaneously is the leading cause of deformation (`E-GEN-504`). Default motion
level 2; level 4 needs a director justification, level 5 needs a human.

## 5. REFERENCES

2–4 per shot, ordered character → environment → palette. More references produce
mush. References are immutable; a regenerated reference gets a new id.

## 6. CANDIDATES AND SEEDS

Generate candidates in one batch with different seeds. Never change the prompt
between candidates — that conflates two variables and destroys the learning
signal (M19 §6).

## 7. COST DISCIPLINE

Flow is the most expensive queue. Never generate before the storyboard gate, and
never before the narration for that scene exists (you cannot know the duration).
Track `waste_ratio` per scene; above 0.35, stop and fix the prompt.

## 8. OUTPUT CONTRACT

```
assets/video/SH-*.mp4 · assets/image/SH-*_still.png
assets/reference/REF-*.png · reports/flow_generation_<scene>.json
```

## 9. FAILURE MODES

| Symptom | Cause | First move |
|---------|-------|-----------|
| Face morphs | motion too high on close-up | motion_reduce to 1 |
| Wrong costume | weak reference | reference_reinforce |
| Extra limbs | complex action | shot_simplify |
| Different person | long prompt diluting identity | front-load subject, shorten |
| Flat look | style profile not applied | re-inject grade/grain language |

## 10. ACCEPTANCE CRITERIA

- Every generation records prompt version, seed, model version, cost.
- No shot exceeds the template's `motion_ceiling`.
- No generation before its narration exists.

**NEXT:** Module 07 — ElevenLabs Voice & Music Guide

**CHANGELOG** v2.1 — Reliability table, motion budget, cost discipline.

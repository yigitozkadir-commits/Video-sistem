# MODULE 12 — AI QUALITY ASSURANCE BIBLE
**Version 2.0 · Layer 3 (Governance) · Status: NORMATIVE**

> This module was referenced by Module 11 but never written. Nine modules depend
> on it. It defines what "good" means numerically, who may declare it, and what
> happens when it is not reached.

---

## 1. MISSION

Convert subjective judgements ("this looks wrong") into scored, reproducible,
machine-actionable verdicts that gate every stage transition in Module 13.

**QA is not a stage. QA is a gate that exists between all stages.**

## 2. THE THREE QA TIERS

| Tier | Name | Executed by | Cost | When |
|------|------|-------------|------|------|
| T1 | **Deterministic Check** | Code (Claude Code) | ~0 | Always, every artifact |
| T2 | **Model Review** | Vision/LLM reviewer | low | Every generative artifact |
| T3 | **Human Review** | Person | high | Only on triggers (§10) |

T1 must pass before T2 runs. T2 must run before T3 is offered.
Never spend a human on something a checksum could have caught.

## 3. QUALITY DIMENSIONS (the 8 axes)

Every artifact is scored on the axes that apply to it. Score 0–100.

| Axis | Code | Applies to | Question |
|------|------|-----------|----------|
| Narrative Fidelity | `NAR` | scene, shot, video, voice | Does it serve the story beat as written? |
| Visual Consistency | `VIS` | image, video | Same character/place/palette as reference? |
| Technical Integrity | `TEC` | all media | Resolution, codec, corruption, artifacts |
| Temporal Sync | `SYN` | timeline, render | Audio/visual/caption alignment |
| Audio Quality | `AUD` | voice, music, mix | Noise, clipping, LUFS, pronunciation |
| Composition | `CMP` | image, video | Framing, headroom, safe areas, rule-of-thirds intent |
| Emotional Fit | `EMO` | voice, music, shot | Does it feel like the target emotion? |
| Compliance | `LEG` | all | Rights, likeness, age-appropriateness |

## 4. SCORING RUBRIC (universal, per axis)

| Band | Score | Meaning | Action |
|------|-------|---------|--------|
| A | 90–100 | Broadcast quality | Accept |
| B | 75–89 | Good, minor flaw | Accept, log finding |
| C | 60–74 | Usable but weak | Retry once; accept second-best if retry ≤ original |
| D | 40–59 | Wrong | Retry with corrective strategy (M15 §11 / M16 §11) |
| F | 0–39 | Broken / unusable | Fail task, classify error, escalate |

**Never invent decimal precision.** Scores are integers, and any score must be
accompanied by at least one concrete observation. A score with no observation is
invalid and must be treated as `null`.

## 5. GATE THRESHOLDS

```yaml
gates:
  shot_accept:      { min_axis: 60, min_weighted: 75, hard_fail: [TEC, LEG] }
  scene_accept:     { min_axis: 65, min_weighted: 78, hard_fail: [TEC, LEG, SYN] }
  master_export:    { min_axis: 70, min_weighted: 82, hard_fail: [TEC, LEG, SYN, AUD] }
weights:
  NAR: 0.25
  VIS: 0.15
  TEC: 0.15
  SYN: 0.15
  AUD: 0.10
  CMP: 0.10
  EMO: 0.07
  LEG: 0.03   # low weight, but it is a hard_fail axis — see below
```

`hard_fail` axes bypass weighting: if any listed axis scores below its band D
floor (40), the gate fails regardless of the weighted total. `LEG` fails at
**any** finding, not at a threshold.

## 6. DETERMINISTIC CHECKS (T1) — the non-negotiable list

**Media**
- File exists, non-zero, hash recorded, mime matches extension
- Video: expected duration ± 0.05 s, fps exact, no black frames > 0.5 s,
  no frozen frames > 1.0 s (unless `intentional_hold: true`)
- Image: min 1024 px on the short edge for reference, 2048 px for hero
- Audio: peak ≤ −1.0 dBTP, integrated loudness −16 LUFS ±1 (stereo web),
  no silence > 2.0 s inside a narration segment, no clipping samples

**Structure**
- Every `scene_id` in `timeline.json` exists in `scene_index.json`
- Every asset referenced exists in `asset_manifest.json` and on disk
- No duplicate IDs, no orphan assets, no dangling dependency edges
- Caption timing within [start, end] of its shot; CPS ≤ 17; line length ≤ 42

**Determinism**
- `model_version`, `seed`, `prompt_version` recorded for every generated asset

Any T1 failure = `E-TEC-*` error, retry allowed, never human-escalated on first
occurrence.

## 7. MODEL REVIEW (T2) — how the reviewer must behave

The reviewer agent receives: the artifact, the **intent** (shot spec + story
beat), and the **references**. It must not see previous scores (avoids anchoring).

Output contract:

```json
{
  "artifact_id": "AST-VID-000412",
  "reviewer": { "model": "…", "version": "…", "run_id": "…" },
  "scores": { "NAR": 84, "VIS": 71, "TEC": 95, "CMP": 80, "EMO": 77 },
  "findings": [
    { "axis": "VIS", "severity": "major",
      "observation": "Character's cloak is blue; reference sheet specifies deep red.",
      "evidence": { "frame": 42, "region": "center-left" },
      "suggested_fix": "regenerate_with_reference",
      "confidence": 0.86 }
  ],
  "verdict": "retry",
  "blocking": false
}
```

**Reviewer rules**
1. Cite evidence (frame number, timecode, word) or the finding is void.
2. Never propose creative changes — only conformance fixes. Creative change is
   the AI Director's authority (M17).
3. Severity ladder: `trivial` → `minor` → `major` → `blocking`.
4. If confidence < 0.6 on a blocking finding, downgrade to `major` and mark
   `needs_human: true`.
5. A reviewer may never review its own generation. Generator ≠ reviewer.

## 8. CONTINUITY QA (cross-artifact)

Continuity is checked at scene close and at act close, not per shot.

- **Character continuity:** face, hair, clothing, age, scars/props vs
  `character_sheet.json`. Drift score > 20 on `VIS` between two shots of the same
  character in the same scene = blocking.
- **Environment continuity:** time of day may only progress forward within a
  scene; weather may not change without a story beat authorising it.
- **Palette continuity:** dominant hue delta between adjacent shots ≤ 25° unless
  the transition is marked `deliberate_contrast`.
- **Voice continuity:** a character's `voice_id` is immutable per project.
- **Pace continuity:** no three consecutive shots with identical duration ±0.2 s
  (machine-gun effect), unless `rhythmic_intent: true`.

## 9. QA REPORT OBJECT

```json
{
  "report_id": "QAR-0007",
  "scope": "scene",
  "target_id": "SC-014",
  "tier": "T2",
  "created_at": "2026-08-05T10:00:00Z",
  "axis_scores": { "NAR": 86, "VIS": 74, "TEC": 92, "SYN": 88, "AUD": 90, "CMP": 79, "EMO": 81, "LEG": 100 },
  "weighted_score": 84.1,
  "gate": "scene_accept",
  "result": "pass_with_findings",
  "findings": [ /* … */ ],
  "retry_history": [ { "attempt": 1, "score": 61, "strategy": "prompt_refine" } ],
  "human_review_required": false,
  "signed_by": "review-agent@v2.0"
}
```

`result` ∈ `pass` · `pass_with_findings` · `retry` · `fail` · `halt`.

## 10. HUMAN REVIEW TRIGGERS (T3)

Escalate to a human when **any** of these is true:

1. `LEG` finding of any severity (rights, likeness, minors, trademarks).
2. Same task failed ≥ 3 times with three *different* retry strategies.
3. Retry improved score by < 5 points across two attempts (plateau).
4. Weighted score sits in 70–78 band at `master_export` (the ambiguity band).
5. Reviewer disagreement: two reviewers differ by > 20 on the same axis.
6. Story deviation flagged by M17 with `deviation_class: material`.
7. Budget for the scene exceeded 150 % of estimate.
8. First scene of a new project (calibration gate) — always human-reviewed.

Human review response is an **Approval object** (M13 §15), never a chat message.

## 11. COMPLIANCE AXIS (`LEG`) — mandatory checks

- Source text: public domain / licensed / user-owned. Record the basis in
  `project.json.rights.source_basis`. Unknown = HALT.
- No depiction of real, identifiable living people as characters without an
  explicit `rights.likeness_clearance` entry.
- No reproduction of a copyrighted illustration style attributed to a named
  living artist by name; use descriptive style language instead (M19 §7).
- Voice cloning only from voices with `voice_license` on record.
- Music: generated only; no reproduction of existing melodies/lyrics.
- Age-appropriateness must match `project.audience_rating`.

`LEG` findings are **never** auto-retried. They stop the branch and go to human.

## 12. QA METRICS (fed to M13 §20 observability)

- `first_pass_yield` — % of artifacts passing without retry (target ≥ 0.65)
- `retry_efficiency` — avg score gain per retry (target ≥ 8 points)
- `human_touch_rate` — % of artifacts reaching T3 (target ≤ 0.08)
- `escape_rate` — findings discovered after export ÷ total (target ≤ 0.02)
- `reviewer_agreement` — mean absolute axis delta between two reviewers

If `escape_rate` rises above target, the T1 check list is wrong — add a check.
That is the only correct response; do not tighten thresholds instead.

## 13. OUTPUT CONTRACT

```
qa/qa_report_<target_id>.json
qa/continuity_report_<act>.json
qa/qa_summary.json            # rollup for the whole project
qa/findings.ndjson            # append-only stream of every finding ever raised
```

## 14. FAILURE MODES

| Mode | Symptom | Handling |
|------|---------|----------|
| Score inflation | Everything scores 85–90, escapes rise | Recalibrate with 10 human-scored anchors |
| Reviewer anchoring | Retry always scores +3 | Hide previous scores; fresh context per review |
| Threshold gaming | Retries stop at exactly 75 | Require ≥ 78 on retry to accept |
| Finding spam | 40 trivial findings per shot | Cap: report top 5 by severity, aggregate rest |

## 15. ACCEPTANCE CRITERIA

- No artifact reaches the timeline without a QA report object.
- No gate passes without an explicit `gate` name and threshold set recorded.
- Every `fail` maps to an error code from M13 §16.
- 100 % of `LEG` findings reach a human.

**NEXT MODULE:** Module 13 — AI Production Operating System

**CHANGELOG**
- v2.0 — Module created (was missing in v1.0). Rubrics, gates, tiers, compliance.

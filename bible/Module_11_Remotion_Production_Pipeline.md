# MODULE 11 — REMOTION PRODUCTION PIPELINE
**Version 2.1 · Layer 2 (Data)**

## 1. ROLE

Remotion is the assembly engine. It makes **no creative decisions**. It executes
`timeline.json` frame-exactly.

## 2. INPUTS / OUTPUTS

**In:** `timeline.json`, `composition.json`, audio stems, `timing_map.json`,
assets, `captions.srt/.ass`, fonts, LUTs.
**Out:** `master.mp4`, `master_archive.mov`, captions, `thumbnail.png`,
`render_manifest.json`.

## 3. FRAME DISCIPLINE

- One fps per project; never mixed (24 / 25 / 30 / 60).
- All durations converted to frames once, at the timeline boundary, with
  `round(seconds * fps)`. Downstream never sees seconds.
- Every asset probed with `ffprobe` before use; expected durations are not trusted.

## 4. AUDIO IS THE MASTER CLOCK

Visual timing follows narration (LAW-3). If a shot is short, hold the last frame
or extend the still — never speed up the audio, never re-time the words.

## 5. CAMERA ANIMATION (in-engine)

Ken Burns, push, pull, pan, tilt, parallax, fade, cross dissolve. These apply to
**stills**; video shots arrive with their motion baked in from M15. Movement must
support the narration and obey the shot's `decision_ref`.

## 6. CAPTIONS

Generated from the word-level timing map, never re-typed. Limits: ≤ 42 chars per
line, ≤ 2 lines, CPS ≤ 17. For 9:16: 3–5 words per line, lower third, inside the
safe area. Word highlighting uses the emphasis metadata from M16.

## 7. TRANSITIONS

Hard cut by default. Fade and cross dissolve where the beat calls for it. Dip to
black **only** at act boundaries — anywhere else it reads as an ending.

## 8. RENDER SETTINGS

Delivery: H.264 MP4, project resolution, AAC, −16 LUFS, −1 dBTP.
Archive: ProRes / DNxHR MOV. Fonts, LUTs and codec versions pinned per node
(M13 §19.2) — mismatch is the top cause of invisible drift in distributed renders.

## 9. PREFLIGHT (mandatory)

Every referenced asset exists, decodes, and has the expected duration; every
caption cue lies inside its shot; no missing font; disk headroom ≥ 3× expected
output. A render started without preflight is `E-REN-703` waiting to happen.

## 10. CHECKPOINTS & RECOVERY

Checkpoint after timeline, audio mix, captions, scene render, master render.
A failed scene requeues whole; partial frames are discarded, never merged.

## 11. QA BEFORE EXPORT

Frame drops, A/V sync, caption timing, missing assets, black frames > 0.5 s,
frozen frames > 1.0 s (unless intentional), colour consistency, total duration
within ±0.05 s of the timeline.

## 12. OUTPUT CONTRACT

```
render/SC-*.mov · output/master.mp4 · output/master_archive.mov
output/captions.srt · output/captions.ass · output/thumbnail.png
render_manifest.json
```

## 13. FAILURE MODES

| Mode | Symptom | Fix |
|------|---------|-----|
| Drift over long renders | A/V out of sync at minute 6 | Frame-derived timing, single fps |
| Node mismatch | Colour/font differs per scene | Pin fonts, LUTs, codec versions |
| Missing asset at render | Crash after 40 minutes | Preflight |
| Caption overflow | Text off-screen on mobile | CPS/line limits + safe areas |

## 14. ACCEPTANCE CRITERIA

- Preflight passes before any render task dispatches.
- Master duration matches the timeline within one frame.
- Deterministic re-render is byte-identical (LAW-5).

**NEXT:** Module 12 — AI Quality Assurance Bible

**CHANGELOG** v2.1 — Preflight gate, frame discipline, caption limits, node pinning.

# MODULE 15 — FLOW ENTERPRISE
**Version 2.0 · Layer 5 (Enterprise) · Role: Cinematography Engine**

> Flow is not a wish machine. It is a camera, a lens, a light kit and a set.
> This module defines the language used to operate it, and the rules that keep
> shot 40 looking like shot 1.

---

## 1. AUTHORITY & LIMITS

**May decide:** prompt surface realisation, seed selection, candidate count,
retry strategy within its ladder, technical parameters.

**May not decide:** what the shot *is* (M17 owns shot design), whether a shot is
needed, story or emotion changes, reference identity.

---

## 2. INPUT CONTRACT

```
shot.json  · scene.json  · character_sheet.json  · style_profile.json
camera_plan.json  · references/{REF-*}  · prompt_version PV-xxxx
```

If any is missing → `E-PLN-401`, task blocked. Flow never improvises a missing
input; a beautiful shot of the wrong thing is worse than no shot.

---

## 3. THE PROMPT DSL

Flow prompts are **assembled**, never hand-written. Nine ordered slots. Order
matters: models weight early tokens more heavily, so identity precedes scenery.

```
[SUBJECT] [ACTION] [ENVIRONMENT] [LIGHTING] [CAMERA] [LENS] [MOTION] [STYLE] [TECHNICAL]
—NEGATIVE—
```

```json
{
  "prompt_version": "PV-0031",
  "slots": {
    "subject":     "a woman in her forties, high cheekbones, dark braided hair under a fur-trimmed headdress, deep red brocade robe",
    "action":      "turns her head slowly toward the tent entrance, expression unreadable",
    "environment": "interior of a felt yurt, low wooden throne, patterned rugs, brass vessels, cold daylight from the smoke hole",
    "lighting":    "single soft top light from the smoke hole, warm firelight fill from frame left, deep shadow falloff",
    "camera":      "slow push in, eye level, subject slightly right of centre",
    "lens":        "85mm equivalent, shallow depth of field, background falls soft",
    "motion":      "minimal: head turn only, fabric settles, dust motes drift",
    "style":       "photoreal historical drama, muted earth palette, fine film grain",
    "technical":   "9:16 vertical, 4 seconds, 24fps cadence, stable framing"
  },
  "negative": "text, watermark, extra fingers, modern objects, plastic skin, warped face, fast motion, camera shake, lens flare, oversaturation",
  "references": ["REF-CHR-001", "REF-ENV-004"],
  "seed": 774411
}
```

**Slot laws**
1. One idea per slot. Two camera moves in `camera` is a defect, not a style.
2. **Motion budget:** a shot has one primary motion. Camera move + subject action
   + environmental motion ≥ 3 simultaneous = `motion collapse` risk (the single
   most common Flow failure, `E-GEN-504`).
3. Never name a living artist or a copyrighted franchise in `style` (M12 §11).
   Describe the look instead.
4. Negative prompt is a standing base + shot-specific additions, never rewritten
   from scratch.
5. Prompts are English (`project.language.prompts`), regardless of narration
   language.

---

## 4. CAMERA DSL

| Token | Use when | Duration floor | Notes |
|-------|----------|----------------|-------|
| `static` | Reflection, dialogue, dread | 2 s | Safest; use more than you think |
| `push_in.slow` | Realisation, growing tension | 3 s | Never combine with subject approach |
| `pull_out.slow` | Isolation, reveal of scale | 3 s | Great for act endings |
| `pan.left/right` | Geography, following movement | 3 s | Needs a subject to motivate it |
| `tilt.up/down` | Scale, power, submission | 2.5 s | Up = awe, down = judgement |
| `tracking` | Journey, urgency | 4 s | Highest failure rate; test first |
| `orbit.slow` | Object of significance | 4 s | Expensive, use once per act |
| `crane/drone` | Establishing, epic geography | 4 s | Never on close-ups |
| `handheld.subtle` | Danger, intimacy, chaos | 2 s | Add grain; never with orbit |
| `parallax` | Still-image scenes (Remotion) | 3 s | Not a Flow move — Ken Burns in M11 |

**Camera grammar rules**
- No two consecutive shots with the same move (M12 §8 pace continuity).
- Move direction should reverse or rest between shots; three pushes in a row
  reads as a mistake.
- A camera move must be motivated by the beat, not by boredom. If M17 cannot
  state the reason in one sentence, the shot is `static`.

---

## 5. LIGHTING DSL

`golden_hour` · `blue_hour` · `harsh_noon` · `overcast_soft` · `moonlight_cool`
· `firelight_warm` · `candlelight_intimate` · `single_window_soft` ·
`volumetric_shafts` · `backlit_silhouette` · `practical_only` · `studio_neutral`

Each carries: key direction, contrast ratio, colour temperature, shadow density.

**Continuity law:** lighting may not change within a scene unless a story event
causes it (a door opens, a lamp is lit, time passes explicitly). Time of day may
only move forward.

---

## 6. LENS DSL

| Token | mm equiv | Feeling | Warning |
|-------|----------|---------|---------|
| `ultrawide` | 16–24 | Vastness, unease, distortion | Never on faces |
| `wide` | 28–35 | Environment + subject | Default establishing |
| `normal` | 40–55 | Neutral, documentary | Safe |
| `portrait` | 85 | Intimacy, separation | Default close-up |
| `tele` | 135–200 | Compression, voyeurism, distance | Needs space |
| `macro` | — | Detail, object significance | One per scene max |

Depth of field follows the lens; do not request `ultrawide` + `shallow depth`.

---

## 7. MOTION & ANIMATION DSL

`motion_intensity` ∈ 0–5.

| Level | Content | Risk |
|-------|---------|------|
| 0 | Still frame, no motion | none (prefer for hero portraits) |
| 1 | Ambient only: cloth, hair, dust, smoke | low |
| 2 | Single small subject action + ambient | low |
| 3 | Subject action + camera move | medium |
| 4 | Multi-subject action or fast camera | **high** |
| 5 | Crowd/combat/complex physics | **avoid — use cuts instead** |

**Rule:** default is 2. Level 4+ requires M17 justification recorded in the shot
spec. Level 5 requires human approval.

**Faces:** at motion ≥ 3 with a close-up, identity drift is likely. Prefer
motion 1–2 for any shot where the character's face is the subject.

---

## 8. STYLE PROFILES

A style profile is a file, not a sentence. It is the single reason forty shots
look like one film.

```json
{
  "style_id": "historical_epic_steppe",
  "palette": { "dominant": ["#6B4A2F", "#8C1F1F", "#C8B18A"], "forbidden": ["neon", "pastel"] },
  "grade": "desaturated warm shadows, cool highlights, film curve",
  "grain": "fine 35mm",
  "lens_set": ["wide", "normal", "portrait"],
  "motion_ceiling": 3,
  "lighting_vocabulary": ["single_window_soft", "firelight_warm", "overcast_soft", "golden_hour"],
  "texture_language": "felt, leather, brass, wool, breath in cold air",
  "forbidden": ["modern objects", "plastic sheen", "anime stylisation", "lens flare"]
}
```

Every prompt inherits the profile; a shot may narrow it, never contradict it. A
contradiction is `E-PLN-402` at plan time, not a Flow problem at run time.

---

## 9. CONSISTENCY SYSTEM (the hard part)

### 9.1 Character memory

`character_sheet.json` per character, built **once**, at P1, before any scene:

```json
{ "character_id": "CHR-001", "name": "Taidula",
  "canonical_refs": ["REF-CHR-001-front", "REF-CHR-001-three-quarter", "REF-CHR-001-profile"],
  "identity_tokens": "high cheekbones, dark braided hair, amber-brown eyes, small scar left brow",
  "wardrobe": { "default": "deep red brocade robe, fur-trimmed headdress",
                "variants": { "travel": "…", "mourning": "…" } },
  "age_range": "38–45", "height_build": "tall, upright",
  "voice_id": "VOI-003",
  "locked": true }
```

**Lock rule:** once `locked: true`, identity tokens and canonical refs may only
change through a human approval object. Wardrobe variants may be added freely.

### 9.2 Reference discipline

- 2–4 references per shot. More references = mush, not fidelity.
- Reference priority order: character → environment → palette. Never send two
  competing character references in one call.
- References are immutable assets (M09 §11). A regenerated reference is a **new**
  `REF-` id, and every shot using the old one keeps using the old one.

### 9.3 Shot-to-shot consistency protocol

1. First shot of a scene establishes the look → becomes `scene_anchor`.
2. Every later shot in the scene receives the anchor frame as an extra reference.
3. After each accepted shot, compute drift vs anchor (palette delta, face
   embedding distance if available). Drift > threshold → retry with
   `reference_reinforce`.
4. Last frame of a scene is stored as `continuity_frame` for any scene declaring
   `continuity_from` (M13 §7).

---

## 10. GENERATION POLICY

| Shot importance | Candidates | Stills | Notes |
|-----------------|-----------|--------|-------|
| Hero (act opening, climax, character intro) | 3 video | 2 | human sees these first |
| Standard | 2 video | 1 | |
| Filler / B-roll | 1 video | 0 | or a still + Ken Burns |
| Reference generation | 4 stills | — | pick 1, lock it |

Candidates are generated **in one batch with different seeds**, never
sequentially with prompt edits — that conflates two variables and destroys the
learning signal for M19 §6.

---

## 11. SCORING & RETRY

Flow output is scored on M12 axes `NAR, VIS, TEC, CMP, EMO`, plus two
Flow-specific sub-axes:

- `MOT` — motion integrity (deformation, morphing, teleporting limbs)
- `IDN` — identity fidelity to the character sheet

**Failure → strategy map**

| Symptom | Likely cause | Strategy |
|---------|-------------|----------|
| Face morphs mid-shot | motion too high on close-up | `motion_reduce` → level 1 |
| Wrong costume/colour | reference weak or contradicted | `reference_reinforce` |
| Extra limbs / physics break | complex action | `shot_simplify` (ask M17) |
| Looks like a different person | identity tokens diluted by long prompt | shorten prompt, front-load subject |
| Flat, video-game look | style profile not applied | re-inject style, add grain/texture language |
| Composition wrong | camera slot ambiguous | rewrite camera slot only |
| Model refusal | content flag | inspect wording; never rephrase to evade a genuine policy — escalate |

**One variable per retry** (M13 §10). If three strategies fail, fall back to
`fallback_still` and log a finding — a 4-second still with a slow push is always
better than a broken video.

---

## 12. COST DISCIPLINE

Flow is the most expensive queue in the system (M13 §4).

- Never generate before storyboard gate approval.
- Never generate a shot whose narration audio does not exist (you cannot know its
  duration — LAW-3).
- Batch by scene to amortise reference upload.
- Track `waste_ratio` per scene; > 0.35 means the prompts are wrong. Stop
  generating and fix the prompt, do not buy more attempts.

---

## 13. OUTPUT CONTRACT

```
assets/video/SH-<scene>-<nn>_v<n>.mp4
assets/image/SH-<scene>-<nn>_still_v<n>.png
assets/reference/REF-*.png                      (immutable)
scenes/SC-nnn/keyframes/                        (first/last frame of each accepted shot)
reports/flow_generation_<scene>.json            (prompt, seed, model, score, cost per attempt)
```

`flow_generation_*.json` is the training data for the prompt library (M19 §6).
Every field is mandatory; a generation without a recorded prompt version is
unusable knowledge and counts as waste.

---

## 14. FAILURE MODES

| Mode | Symptom | Fix |
|------|---------|-----|
| Prompt drift | Shot 30 prompts look nothing like shot 1 | Assemble from DSL slots, never edit prose |
| Reference soup | 8 references, output resembles none | Cap at 4, prioritise |
| Seed roulette | Endless reseeding with no analysis | Max 2 seed variations, then change a slot |
| Style leak | One scene suddenly cinematic-teal | Style profile inheritance check at plan time |
| Motion greed | Every shot has a camera move | Motion budget + camera grammar rules |
| Silent aspect mismatch | 16:9 generated for a 9:16 project | Technical slot is mandatory; T1 checks dimensions |

---

## 15. ACCEPTANCE CRITERIA

- Every shot traces to a prompt version, seed, model version and reference set.
- No character appears before its sheet is locked.
- No accepted shot violates the style profile's `forbidden` list.
- Drift vs scene anchor within threshold for every accepted shot.
- `waste_ratio` reported per scene.

**NEXT MODULE:** Module 16 — ElevenLabs Enterprise

**CHANGELOG**
- v2.0 — Nine-slot prompt DSL, camera/lens/lighting/motion grammars, motion
  budget, consistency protocol with anchors and drift, symptom→strategy map.
- v1.0 — Initial outline.

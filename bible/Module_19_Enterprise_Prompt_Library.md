# MODULE 19 — ENTERPRISE PROMPT LIBRARY
**Version 2.0 · Layer 7 (Application)**

> A pile of 1000 prompts in a document is not a library — it is a landfill.
> A library is: addressable, versioned, composable, measured, and improvable.
> This module defines that system, plus the seed set it starts from.

---

## 1. WHY PROMPTS MUST BE OBJECTS

In v1.0 prompts lived inside prose. That makes it impossible to answer the only
questions that matter: *which prompt produced this shot, how well does it score,
and is version 4 better than version 3?* Every prompt is therefore a file with an
id, referenced by `PV-` in every task (M13 §3).

---

## 2. PROMPT OBJECT

```json
{
  "prompt_id": "PV-0031",
  "family": "flow.shot.closeup.realisation",
  "tool": "flow",
  "version": 3,
  "supersedes": "PV-0022",
  "language": "en-US",
  "variables": ["subject", "environment", "lighting", "lens", "motion_level", "style_profile"],
  "template": "{subject}. {action}. {environment}. {lighting}. {camera}. {lens}. {motion}. {style}. {technical}",
  "constraints": { "motion_level_max": 2, "requires_reference": true },
  "negative_base": "text, watermark, extra fingers, warped face, plastic skin, modern objects",
  "stats": { "uses": 46, "avg_score": 83.1, "first_pass_yield": 0.72, "avg_cost": 31 },
  "status": "active",
  "notes": "Front-loading identity tokens raised IDN by ~9 points vs PV-0022."
}
```

`status` ∈ `draft` · `active` · `deprecated` · `retired`.
A prompt is never edited in place — a change creates a new version. This is what
makes M12's scores comparable over time.

---

## 3. NAMING & TAXONOMY

```
<tool>.<artifact>.<situation>.<variant>
```

| Tool | Artifacts |
|------|-----------|
| `flow` | shot, still, reference, upscale |
| `eleven` | narration, dialogue, music, ambience, sfx |
| `claude` | ingest, ocr, classify, scene_candidate, timeline, preflight |
| `orchestrator` | story_analysis, beat_map, script, adaptation |
| `director` | shot_design, camera_choice, rhythm_review, decision_audit |
| `review` | visual_qa, audio_qa, continuity_qa, compliance_qa |
| `remotion` | composition, caption, transition |
| `ffmpeg` | probe, concat, normalize, encode |

Examples: `flow.shot.wide.establishing.golden_hour`,
`eleven.narration.beat.grief`, `review.visual_qa.identity_drift`.

---

## 4. HOW THE LIBRARY REACHES 1000+ (composition, not copy-paste)

The library is **generated combinatorially** from small, curated axes. This is why
it scales and why it stays consistent.

```
flow.shot = shot_type(9) × camera_move(10) × lighting(12) × emotion(10)
```

9 × 10 × 12 × 10 = **10,800 possible** shot prompts, of which the constraint
matrix (M15 §4 duration floors, §7 motion budget, template `camera_vocabulary`)
leaves a few hundred legal for any given project. Add:

| Family | Curated axes | Realised prompts |
|--------|--------------|------------------|
| `flow.shot.*` | shot type × move × lighting × emotion | ~450 legal combinations |
| `flow.still.*` | subject class × composition × lighting | ~120 |
| `flow.reference.*` | character/env/object × angle set | ~40 |
| `eleven.narration.*` | beat function(11) × emotion(10) | ~110 |
| `eleven.music.*` | mood(12) × instrumentation(8) | ~96 |
| `eleven.ambience/sfx.*` | location(15) × time/weather(6) | ~90 |
| `claude.*` | 30 hand-written operational prompts | 30 |
| `orchestrator.*` | 25 | 25 |
| `director.*` | 20 | 20 |
| `review.*` | 24 (4 tiers × 6 axes) | 24 |
| `remotion/ffmpeg.*` | 20 | 20 |
| **Total** | | **~1,025** |

**The axes are the library; the 1,025 are its expansion.** Maintain 60 axis
entries, not 1,000 paragraphs.

---

## 5. SEED SET (canonical examples — one per family)

### 5.1 `flow.shot.closeup.realisation` (PV-0031)
```
{identity_tokens}, {wardrobe}. {micro_action, one movement only}.
{environment, three concrete nouns}. {lighting_token expanded to key + fill + falloff}.
Slow push in, eye level, subject slightly off centre.
85mm equivalent, shallow depth of field.
Minimal motion: {one ambient element} only.
{style_profile.grade}, {style_profile.grain}, {palette words}.
{aspect_ratio}, {duration}s, stable framing.
NEGATIVE: text, watermark, extra fingers, warped face, plastic skin, fast motion,
camera shake, modern objects, {style_profile.forbidden}
```

### 5.2 `flow.shot.wide.establishing` (PV-0044)
```
{environment as the subject: architecture, terrain, scale cue}. {human figure
small in frame for scale, optional}. {weather and air: haze, dust, snow}.
{lighting_token}. Static wide, or slow pull out if the beat is isolation.
28mm equivalent, deep focus.
Motion: environmental only — {smoke / grass / cloth / water}.
{style_profile}. {aspect_ratio}, {duration}s.
NEGATIVE: {negative_base}, distorted horizon, duplicated architecture, tilted frame
```

### 5.3 `flow.reference.character.sheet` (PV-0007)
```
Character reference sheet: {identity_tokens}, {wardrobe.default}, {age_range}.
Neutral expression, even studio lighting, plain neutral background.
Three views in one image: front, three-quarter, profile. Full head and shoulders.
Consistent proportions across views. High detail on {distinguishing features}.
NEGATIVE: dramatic lighting, background scenery, props, motion blur, text, multiple people
```

### 5.4 `eleven.narration.beat.revelation` (PV-0102)
```json
{ "text": "{beat_text}",
  "intent": "the truth lands; restrained, not theatrical",
  "delivery": { "stability": 0.5, "style": 0.3, "speed": 0.93 },
  "emphasis": ["{key_word}"],
  "pause_before_ms": 800, "pause_after_ms": 1400, "breath_before": true }
```
*Direction note: the pause after carries the meaning. Do not let the next beat
start under it.*

### 5.5 `eleven.music.cue.restrained_tension` (PV-0140)
```
Sparse, slow, unresolved. Low sustained strings with a single repeating figure.
62 BPM, D minor, no percussion, no melody in the 200–2000 Hz vocal band.
Intensity: begins at 0.2, rises to 0.5 by two-thirds, falls to 0.15 before the end.
3-second fade in, 4-second tail out. Loopable middle section.
Must not: cymbal swells, orchestral hits, resolution to major.
```

### 5.6 `claude.classify.book_image` (PV-0210)
```
You are cataloguing an image extracted from a book for a production pipeline.
Given the image, its page context and nearby caption, output ONLY JSON matching
image_catalog.schema.json.
Score narrative_relevance, visual_quality, resolution_adequacy, reuse_potential
and reference_value 0–100. Every score must be accompanied by one concrete
observation. Choose exactly one disposition from the six in Module 14 §6.
If the rights basis is unknown, disposition must be HOLD_LEGAL.
Do not describe the image poetically. Do not guess the story.
```

### 5.7 `orchestrator.story.beat_map` (PV-0301)
```
Segment this scene text into beats. A beat is 1–4 sentences with one intention.
For each beat output: function (setup|inciting|complication|reversal|revelation|
decision|confrontation|consequence|resolution|transition|breath), emotion
{from,to}, information_delivered (one sentence), attention_target
(face|two_people|place|object|movement), weight 0–1.
Do not invent events. Do not merge beats to reach a target count.
At most 20% of beats may have weight > 0.8.
Output JSON only, matching beat_map.schema.json.
```

### 5.8 `director.shot_design` (PV-0401)
```
For each beat, design shots using Module 17 §6–§7 decision trees.
For every shot you must output: camera, lens, motion_level, duration, and a
one-sentence reason. If your reason contains "to make it more interesting",
replace the camera with static.
Query decision memory for the same question in this project and cite precedent
ids you followed or deliberately broke.
Respect the template's camera_vocabulary and motion_ceiling.
Output JSON only, matching shot_plan.schema.json.
```

### 5.9 `review.visual_qa.shot` (PV-0501)
```
You are reviewing a generated shot against its intent. You did not create it.
Inputs: the video, the shot spec, the character sheet, the scene anchor frame.
Score NAR, VIS, TEC, CMP, EMO, MOT, IDN as integers 0–100. Each score requires at
least one observation citing a frame number or timecode. Findings only about
conformance to the spec — never propose creative changes.
If confidence on a blocking finding is below 0.6, downgrade to major and set
needs_human true. Output JSON only, matching qa_report.schema.json.
```

### 5.10 `remotion.caption.style` (PV-0601)
```
Generate caption cues from the word-level timing map. Never re-type narration.
Max 42 characters per line, max 2 lines, CPS ≤ 17. Break on clause boundaries.
For 9:16: 3–5 words per line, positioned in the lower third above the safe area.
Highlight the emphasised word from the acting metadata if word highlighting is on.
Output SRT and ASS.
```

### 5.11 `ffmpeg.normalize.master` (PV-0701)
```
Two-pass loudness normalisation to integrated -16 LUFS, true peak -1.0 dBTP,
LRA target 11. Do not resample. Preserve original sample rate (48 kHz).
Report measured values before and after; fail if post-measurement deviates more
than 0.5 LU from target.
```

---

## 6. PROMPT SCORING & EVOLUTION

Every generation writes back: `prompt_id, model, seed, QA axis scores, cost,
accepted`. From this the library computes per prompt:

- `avg_score`, `first_pass_yield`, `avg_cost`, `waste_ratio`
- per-axis weakness profile (e.g. "strong NAR, weak IDN")

**Promotion rule:** a new version replaces the active one only if, over ≥ 10 uses,
it improves `first_pass_yield` by ≥ 0.05 **or** `avg_score` by ≥ 4 points, without
increasing cost by more than 15 %.

**Retirement rule:** `first_pass_yield` < 0.4 over 15 uses → `deprecated`, and the
system stops selecting it automatically.

**A/B rule:** never test two prompt versions on different scenes — the scenes
differ. Test on the same shot, same seed set, same references.

---

## 7. SAFETY & RIGHTS RULES FOR PROMPTS

1. Never name a living artist, studio, franchise, or brand as a style source.
   Describe the visual properties instead.
2. Never describe a real, identifiable living person as a character.
3. Never reproduce lyrics, poems, or copyrighted text inside a prompt.
4. Never attempt to rephrase around a model refusal on genuine policy grounds —
   escalate to human (M15 §11).
5. Children's content: no dread lighting, no threat imagery, no ambiguous adults
   in isolation with children.
6. All prompts are stored in English; audience-facing text is never generated by
   a prompt written in the wrong locale (M16 §3).

---

## 8. OUTPUT CONTRACT

```
prompts/PV-*.json                  every prompt version
prompts/axes/*.json                curated axes (shot types, moves, lighting, emotions…)
prompts/index.json                 family → active version map
prompts/stats.json                 rolling performance per prompt
prompts/CHANGELOG.md
```

## 9. ACCEPTANCE CRITERIA

- No generation task dispatches without a `PV-` reference.
- No prompt is edited in place; every change is a new version.
- Every family has exactly one `active` version at a time.
- Stats update after every accepted or rejected generation.

**NEXT MODULE:** Module 20 — AI Audiobook Studio OS v1

**CHANGELOG**
- v2.0 — Prompt-as-object model, combinatorial axes, scoring/promotion rules,
  canonical seed set, rights constraints.

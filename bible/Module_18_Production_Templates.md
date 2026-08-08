# MODULE 18 — PRODUCTION TEMPLATES
**Version 2.0 · Layer 7 (Application)**

> A template is a **preset for every knob in Modules 15, 16 and 17 at once**.
> Choosing a template should decide 80 % of the production before the first
> prompt is written.

---

## 1. TEMPLATE OBJECT

```json
{
  "template_id": "TPL-childrens-book",
  "extends": null,
  "director": {
    "pace": { "avg_shot_s": 4.5, "range": [3, 7] },
    "still_video_ratio": 0.55,
    "motion_ceiling": 2,
    "silence_per_act": 1,
    "beat_weight_cap": 0.85,
    "camera_vocabulary": ["static", "push_in.slow", "pan.right", "tilt.up"]
  },
  "visual": {
    "style_profile_ref": "style/storybook_watercolour.json",
    "palette": ["warm pastel", "high value", "soft edges"],
    "lens_set": ["wide", "normal"],
    "lighting": ["single_window_soft", "golden_hour", "overcast_soft"],
    "forbidden": ["photoreal skin", "harsh shadow", "gore", "night horror"]
  },
  "audio": {
    "narrator": { "stability": 0.55, "style": 0.35, "speed": 0.95, "wpm": 130 },
    "music": { "density": "high", "instruments": "celesta, harp, light strings", "loudness_under_speech_db": -20 },
    "ambience": "gentle, always present",
    "silence_max_s": 1.5
  },
  "qa_overrides": { "gates": { "shot_accept": { "min_weighted": 78 } },
                     "audience_rating": "children" },
  "budget_profile": { "credits_per_minute": 220 }
}
```

Templates may `extends` another template and override selectively.
`qa_overrides` may only make gates **stricter**, never looser.

---

## 2. THE TWELVE TEMPLATES

### 2.1 Children's Book (`TPL-childrens-book`)
Pace 4–6 s · stills 55 % · motion ≤ 2 · warm pastel · narrator 130 wpm, high pitch
variation · music near-continuous but very low under speech · silence short (kids
read silence as "it stopped") · absolutely no dread lighting · faces always fully
visible, never in shadow · QA: `audience_rating: children` blocks any frightening
imagery finding.

### 2.2 Documentary (`TPL-documentary`)
Pace 5–8 s · stills 65 % (archive-driven) · motion ≤ 2 · neutral grade · narrator
145 wpm, low style, high stability · music sparse, exits under every fact ·
frequent hold on maps/diagrams with 1.6× reading margin · lower thirds allowed ·
QA weights: `NAR` 0.30, `EMO` 0.03 — accuracy beats feeling.

### 2.3 Historical Epic (`TPL-historical-epic`)
Pace 4–7 s · stills 45 % · motion ≤ 3 · desaturated warm shadows, film grain ·
lens: wide + portrait, avoid tele · narrator 140 wpm, grave · music: low drone +
sparse strings, cuts before every revelation · long silences allowed (2.5 s) ·
period-accuracy check added to T2 review (no modern objects, correct materials).

### 2.4 Anime (`TPL-anime`)
Pace 2.5–5 s (faster cuts) · stills 40 % but with strong parallax · motion ≤ 3 ·
saturated palette, hard rim light, speed lines allowed · impact frames on beat
climaxes · narrator higher energy · music: melodic, present · **never** name a
studio or franchise in prompts — describe the look (M12 §11).

### 2.5 Family Animation (`TPL-family-animation`)
Pace 3.5–6 s · stills 45 % · motion ≤ 3 · bright, high-key, rounded forms,
expressive faces · narrator warm, 135 wpm · music orchestral, thematic recurrence
required (motif returns ≥ 3×) · comedy beats get a 400 ms post-hold for the laugh.

### 2.6 Fantasy (`TPL-fantasy`)
Pace 4–7 s · stills 50 % · motion ≤ 3 · volumetric light, atmospheric haze,
jewel-tone palette · wide establishing shots at every new location · narrator
warm-grave, 140 wpm · music: choir pads + strings, big at act openings, silent at
revelations.

### 2.7 Dark Fantasy (`TPL-dark-fantasy`)
Pace 5–9 s (slower, heavier) · stills 55 % · motion ≤ 2 · low key, single source,
crushed shadows, desaturated with one accent hue · faces often partly in shadow ·
narrator 125 wpm, low, restrained · music: drones, sub-bass, near-silence ·
silences long (2.5 s) · QA: violence limited to implication; `LEG` audience check.

### 2.8 Cyberpunk (`TPL-cyberpunk`)
Pace 3–5 s · stills 40 % · motion ≤ 3 · practical neon, wet reflective surfaces,
high contrast, cyan/magenta with one warm break · anamorphic-feel wide + tele ·
narrator dry, 150 wpm · music: pulse synth, rhythmic bed · caution: neon +
motion 4 is a reliable artifact generator — cap motion at 3.

### 2.9 Noir (`TPL-noir`)
Pace 4–8 s · stills 60 % · motion ≤ 1 (stillness is the style) · hard key,
venetian shadow, monochrome or near-monochrome · lens: normal + portrait ·
narrator 135 wpm, wry, close-mic intimacy · music: sparse piano/upright bass,
mostly absent · silence used constantly.

### 2.10 Sci-Fi (`TPL-scifi`)
Pace 4–7 s · stills 45 % · motion ≤ 3 · clean geometry, cold key with warm
practicals, scale contrast (tiny human, huge structure) · wide + ultrawide for
scale, portrait for interiors · narrator neutral-precise, 145 wpm · music:
textural pads, low melody · diagrams and readouts get reading margin.

### 2.11 Fairytale (`TPL-fairytale`)
Pace 4.5–7 s · stills 60 % · motion ≤ 2 · storybook illustration look, soft edges,
gold and forest green · symmetrical composition · narrator 130 wpm, "once upon a
time" cadence with strong beat pauses · music: harp, flute, music box motif ·
repetition of framing is *intentional* here — the rhythm constraint in M17 §6 is
relaxed to "at most three consecutive identical framings".

### 2.12 Vertical Shorts (`TPL-vertical-short`)
9:16 · total 45–90 s · pace 2–4 s · stills 50 % · motion ≤ 2 · hook in the first
2 s (M17 §11) · captions always on, large, 3–5 words per line · narrator 155 wpm ·
music present throughout at low level · one silence maximum, used as the hook
turn · QA adds a `HOOK` check: does second 0–2 state the promise?

---

## 3. TEMPLATE SELECTION

```
audience is children?              → childrens-book | family-animation | fairytale
factual / educational source?      → documentary
real historical events?            → historical-epic (documentary if non-narrative)
speculative future tech?           → scifi | cyberpunk (cyberpunk if urban + noir tone)
magic present?                     → fantasy (dark-fantasy if the tone is dread)
crime / moral ambiguity / 1st person? → noir
stylised Japanese-influenced source? → anime
output < 90 s and vertical?        → vertical-short (composes on top of any other)
```

`vertical-short` is a **modifier** template: it `extends` any base template and
overrides pace, captions and duration.

---

## 4. WHAT A TEMPLATE MAY NOT DO

- Loosen a QA gate (§1).
- Override rights or audience rating rules.
- Remove the narration-as-clock law.
- Set `motion_ceiling` above 4.
- Disable human approval on first scene or master export.

---

## 5. CUSTOM TEMPLATE CREATION

1. Start from the nearest existing template with `extends`.
2. Change no more than 5 fields in the first pass.
3. Produce one calibration scene; human-review it (M12 §10 trigger 8).
4. Adjust, then lock the template with a version and a name.
5. A template becomes reusable Knowledge Base material only after 3 successful
   projects (M13 §18 promotion rule).

---

## 6. OUTPUT CONTRACT

```
templates/TPL-*.json
style/*.json                     (style profiles referenced by templates)
project.json → template_ref      (a project names exactly one base template)
reports/template_conformance.md  (per act: where the render drifted from the template)
```

## 7. ACCEPTANCE CRITERIA

- Every project names a template; no project runs on defaults.
- Template conformance is reported per act (pace, still ratio, motion levels).
- No template override loosens a gate.

**NEXT MODULE:** Module 19 — Enterprise Prompt Library

**CHANGELOG**
- v2.0 — Template object model, 12 full presets, selection tree, modifier templates.

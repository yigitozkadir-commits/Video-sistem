# MODULE 05 — STORYTELLING ENGINE & NARRATIVE INTELLIGENCE
**Version 2.1 · Layer 1**

## 1. ROLE

Turn raw book text into a structured narrative model that downstream modules can
reason about: acts, scenes, beats, characters, motifs, and the emotional curve.

## 2. THE NARRATIVE MODEL

```
BOOK → ACTS → SCENES → BEATS
        │        │        └─ function, emotion, weight, attention_target (M17 §4)
        │        └─ location, time, characters, continuity_from
        └─ dramatic question, turning point, resolution
```

An act is not a chapter. Acts are defined by the change in the dramatic question,
and there are usually 3–5 in an audiobook episode regardless of chapter count.

## 3. EXTRACTION TARGETS

| Element | How it is identified | Used by |
|---------|---------------------|---------|
| Characters | NER + coreference; merged by alias table | M15 sheets, M16 voices |
| Locations | place lexicon + prepositional context | scene grouping, ambience |
| Time markers | temporal expressions | continuity rules |
| Motifs | repeated concrete nouns/images (≥ 3 occurrences) | M17 §12 recurrence |
| Emotional curve | per-beat valence/arousal | pacing, music, silence |
| Dramatic questions | what the reader wants answered | act boundaries |

## 4. THE EMOTIONAL CURVE

Emit a per-beat curve. Two derived checks:

- **Monotony check** — if the curve varies less than 0.15 over an act, the
  adaptation is flat; ask for cuts, not for louder music.
- **Whiplash check** — a jump over two steps on the emotion ladder without a
  `breath` beat between is a defect (M16 §5).

## 5. CHARACTER MODEL

```json
{ "character_id":"CHR-001","name":"…","aliases":["…"],
  "first_appearance":"SC-002","scenes":["SC-002","SC-014"],
  "function":"protagonist|antagonist|ally|witness|narrator",
  "described_traits":["…"], "speech_register":"formal|plain|archaic|childlike" }
```

`described_traits` may contain **only** what the text says. Anything the model
imagines belongs in the character sheet (M15 §9.1) as an explicit invention, and
is flagged for human confirmation.

## 6. ADAPTATION FOR AUDIO+VIDEO

- Interior monologue → narration; it does not need a visual literal.
- Long description → compress to one image and one sentence; the picture is
  doing the describing now.
- Dialogue-heavy passages → keep the dialogue, cut the attributions ("he said")
  where the voice already carries the speaker.
- Lists and genealogies → summarise; they are unlistenable verbatim.

## 7. OUTPUT CONTRACT

```
story/acts.json · story/characters.json · story/locations.json
story/motifs.json · story/emotion_curve.json · beats/beat_map.json
```

## 8. FAILURE MODES

| Mode | Symptom | Fix |
|------|---------|-----|
| Chapter=scene | 40 s scenes and 6 min scenes side by side | Length constraints (M14 §8) |
| Character merge failure | Same person as two characters | Alias table, human confirms |
| Invented traits | Video shows a beard the book never mentions | Text-only traits rule |
| Flat curve | Every scene the same temperature | Monotony check |

## 9. ACCEPTANCE CRITERIA

- Every character has a first appearance and an alias set.
- Emotion curve exists per beat and passes both checks.
- Every motif recurs at least twice in the final cut (M17 §12).

**NEXT:** Module 06 — Google Flow Production Guide

**CHANGELOG** v2.1 — Narrative model, curve checks, adaptation rules.

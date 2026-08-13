# MODULE 07 — ELEVENLABS VOICE & MUSIC GUIDE
**Version 2.1 · Layer 1 (Tool Guide) · Deep spec: M16**

## 1. ROLE

Practical operation of the audio provider. Acting direction, silence design and
mix targets live in M16.

## 2. THE FOUR PARAMETERS

| Parameter | Raise it when | Lower it when |
|-----------|---------------|---------------|
| stability | voice wobbles, identity drifts | delivery is flat and robotic |
| similarity | voice drifts from the reference | output sounds strained |
| style | delivery is lifeless | delivery is theatrical |
| speed | (rarely) | (rarely — cut words instead) |

**One parameter per retry.** Two changes at once teach you nothing.

## 3. SEGMENTATION

Generate per beat, max 45 s, boundaries on punctuation. Join with *measured
digital silence*, never by naive concatenation of model output (breath tails vary
and produce audible seams).

## 4. PRONUNCIATION

Build the pronunciation map at ingest, decide each proper noun once, verify the
first occurrence by ear. This single practice removes the most common re-record
in historical and fantasy material.

## 5. SSML

Only `break`, `emphasis`, `prosody rate|pitch`, `phoneme`. Max 3 tags per
sentence. Bad pacing is fixed with better sentences, not more markup.

## 6. MUSIC

One cue per scene; enters after the scene establishes, exits before the
revelation. Melody must stay out of the 200–2000 Hz vocal band during narration —
that band, not the fader, is why music "feels loud".

## 7. LEVELS

Narration 0 dB reference at −16 LUFS; music under speech −18 to −22 dB; ambience
−18 to −24 dB; SFX −8 to −12 dB; true peak ≤ −1.0 dBTP.

## 8. OUTPUT CONTRACT

```
assets/audio/NAR-*.wav · MUS-*.wav · AMB-*.wav · SFX-*.wav
audio/timing_map.json · audio/pronunciation_map.json · audio/mix_report.json
```

## 9. FAILURE MODES

| Symptom | Cause | Fix |
|---------|-------|-----|
| Name said three ways | no pronunciation map | build it once, at ingest |
| Seam between segments | naive concatenation | measured silence + ambience bed |
| "Can't hear the words" | music in the vocal band | 2–3 kHz dip, sidechain |
| Scene 12 quieter than 3 | per-file loudness | integrated LUFS per scene |

## 10. ACCEPTANCE CRITERIA

- Every segment returns a word-level timing map.
- Every proper noun exists in the pronunciation map.
- Loudness variance across scenes ≤ 1 LUFS.

**NEXT:** Module 08 — Prompt Engineering Bible

**CHANGELOG** v2.1 — Parameter heuristics, segmentation, vocal-band rule.

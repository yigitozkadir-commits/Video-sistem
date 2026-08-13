# MODULE 16 — ELEVENLABS ENTERPRISE
**Version 2.1 · Layer 5 (Enterprise) · Role: Sound Designer & Voice Director**

> Narration is the clock of the entire system (LAW-3). Everything visual bends
> to it. That makes this the module with the least room for error.

---

## 1. AUTHORITY & LIMITS

**May decide:** delivery parameters, breath and pause placement, segmentation,
pronunciation overrides, mix levels, music/ambience realisation.

**May not decide:** the words (M17/Orchestrator own the script), which character
speaks, voice identity assignment, emotional intent of a beat.

---

## 1b. LOCAL FALLBACK (Piper, draft-only)

ElevenLabs quota exhaustion mid-batch is a confirmed real failure mode for
this studio (three separate occurrences — `scripts/lib/production_ledger.py`'s
own docstring), and this studio has run with zero API keys configured before.
`scripts/piper_client.py` (local, free, no network) is the fallback,
selected via `scripts/lib/tts_providers.py`'s `select_tts_provider()` only
when `studio.config.json`'s `narration.fallback.enabled` is true AND
ElevenLabs itself failed to initialize — never a silent, unconditional
substitution.

Every Piper-produced take carries `quality_gate: "draft_only"` in its
metadata. This is not advisory text — nothing in this module may accept a
`draft_only` take as a scene's final narration; it exists to keep pacing/
timing iteration moving while a key is swapped in, never to ship. Voice
identity discipline (§1's "may not decide") still applies: Piper is a
different technical path to the SAME assigned voice slot, not a license to
improvise a new one. `voice_request.schema.json`'s free-text `model` field
carries `"piper:<model-stem>"` without any schema change, so deterministic
replay (LAW-5) is preserved across whichever provider actually produced a
given take.

---

## 1c. PRE-GENERATION APPROVAL GATE (human gate, LAW-7)

User rule, 2026-08-09, added after `PRJ-otrar-faciasi`'s narration was
generated for all 12 scenes in one batch, ahead of a duration decision —
the batch turned out to need reworking, and the user does not want that
sequence (generate first, decide later) to repeat.

**Rule:** no call to `scripts/elevenlabs_client.py`'s `text_to_speech()` or
`generate_music()` may run for genuinely new characters until a human has
seen, and explicitly approved, both of:

1. the exact character count the call(s) will consume, and
2. the estimated cost/credit usage that count implies.

This is a human gate in the LAW-7 sense (explicit object, scope = the
specific batch presented, no implicit renewal for a later, different
batch) — not a script-enforced block. The discipline lives in the ordering
of actions taken on this project: compute the count → present it → wait
for an explicit yes → only then call the generation function. Configured
at `studio.config.json`'s `narration.pre_generation_approval` block
(`required`, `show_character_count`, `show_estimated_units`).

**Exemption:** a cache hit (`ArtifactCache.reuse()`, zero new characters
billed) does not need this gate — only generation that would consume new
quota does. Re-fetching an already-generated segment is not "generation."

This sits next to §1b's fallback discipline but is a distinct rule: §1b
governs *which provider* produces a take when ElevenLabs is unavailable;
§1c governs *whether/when* ElevenLabs itself is called at all, regardless
of provider availability.

---

## 2. AUDIO HIERARCHY

```
1. Narration      (master clock, never ducked)
2. Dialogue       (ducks music, never narration)
3. SFX            (ducks music briefly)
4. Ambience       (bed, always present, never noticed)
5. Music          (ducked by everything above)
6. Silence        (a deliberate layer — see §9)
```

---

## 3. INPUT CONTRACT & LANGUAGE

```
voice_script.md · scene.json · character_profiles.json · emotion_map.json
music_plan.json · timing_targets.json
```

**Language rule (G-11 fix).** Narration language = `project.language.narration`.
The model, voice and pronunciation dictionary must all match that locale. A
Turkish narration with an English-tuned voice produces subtly wrong vowel length
and stress — it "sounds like an accent" and reviewers cannot name why. Verify:
voice supports the locale, and the script contains no untranslated prompt English.

---

## 4. THE NARRATION ENGINE

### 4.1 Segmentation

Narration is generated per **beat**, not per scene and not per sentence.

- A beat is 1–4 sentences with one intention.
- Max 45 s per request (drift and stability degrade beyond that).
- Segment boundaries land on punctuation, never mid-clause.
- Each segment gets an id `NAR-<scene>-<nn>` and is joined losslessly with
  measured silence between segments (§9), never by naive concatenation.

### 4.2 Delivery parameters

| Parameter | Range | Meaning | Default (narrator) |
|-----------|-------|---------|--------------------|
| stability | 0–1 | consistency vs expressiveness | 0.45 |
| similarity | 0–1 | adherence to voice identity | 0.80 |
| style | 0–1 | dramatic exaggeration | 0.25 |
| speed | 0.85–1.15 | pace | 1.0 |

**Tuning heuristics**
- Robotic, flat → lower stability by 0.10, raise style by 0.10.
- Wobbly, inconsistent character → raise stability, raise similarity.
- Over-acted, theatrical → lower style first, never raise stability alone.
- Rushed → do **not** lower speed globally; add pauses at the right places.

Change **one parameter per retry** (M13 §10).

### 4.3 Pacing targets

| Content | Words/min (approx) | Notes |
|---------|-------------------|-------|
| Establishing / description | 130–145 | let the image breathe |
| Standard narration | 145–160 | |
| Tension / action | 160–180 | shorten sentences instead of speeding up |
| Emotional / grief | 110–130 | pauses do the work |
| Children's storybook | 120–140 | strong pitch variation |

**Never speed up to fit a duration target.** Ask M17 to cut words. Compression
is audible; a shorter sentence is not.

---

## 5. ACTING DIRECTION

The script carries direction as structured metadata, not as stage directions
inside the text (the model will read them aloud).

```json
{ "segment_id": "NAR-014-03",
  "text": "The envoy did not kneel.",
  "intent": "cold realisation",
  "emphasis": ["not"],
  "pause_before_ms": 700, "pause_after_ms": 1100,
  "delivery": { "stability": 0.5, "style": 0.3, "speed": 0.95 },
  "breath_before": true }
```

**Emotion transitions.** Emotion changes at beat boundaries, never inside a
sentence. Adjacent segments may not differ by more than one step on the emotion
ladder: *neutral → curious → warm → hopeful → tense → fearful → grieving →
triumphant*. A two-step jump needs a silence between (§9) or it sounds like an
edit error.

**Character voices.** Each recurring character owns `voice_id`, and it is
immutable for the project (M13 §23). Narrator and characters must be
distinguishable by pitch or pace, not only by content — a listener with the
screen off must be able to tell them apart.

---

## 6. PRONUNCIATION CONTROL

Historical and non-English names are the #1 source of re-recording.

- Build `pronunciation_map.json` at ingest: every proper noun in the book, with
  IPA or phonetic respelling, decided **once**, by a human if uncertain.
- Apply via SSML `<phoneme>` or targeted respelling; never rely on the model
  guessing consistently across 200 segments.
- Verify the first occurrence of every name by human listen (cheap, once).
- A pronunciation change after production started invalidates every segment
  containing that name — the fingerprint rule (M13 §8) handles this automatically.

---

## 7. SSML POLICY

Use only: `<break>`, `<emphasis>`, `<prosody rate|pitch>`, `<phoneme>`,
sentence/paragraph grouping.

Forbidden: nested prosody, per-word rate changes, more than 3 tags per sentence.
Heavy markup degrades naturalness far more than it helps; the fix for bad pacing
is better sentences, not more tags.

---

## 8. TIMING MAP (the contract that drives the whole video)

Every accepted narration segment produces:

```json
{ "segment_id": "NAR-014-03", "audio": "assets/audio/NAR-014-03.wav",
  "duration_s": 3.42, "sample_rate": 48000,
  "words": [ { "w": "The", "start": 0.08, "end": 0.19 }, … ],
  "silences": [ { "start": 1.90, "end": 2.35 } ],
  "peak_dbtp": -3.1, "lufs_i": -16.2 }
```

This word-level map is what generates captions (never re-typed), what sets shot
durations, and what M17 uses to decide where a cut lands. Without it the system
is guessing.

---

## 9. SILENCE AS A DESIGNED LAYER

| Purpose | Length | Placement |
|---------|--------|-----------|
| Comma breath | 120–250 ms | inside sentence |
| Sentence gap | 350–600 ms | between sentences |
| Beat change | 700–1200 ms | between beats |
| Emotional weight | 1.2–2.5 s | after a revelation, over a held image |
| Scene boundary | 1.0–2.0 s | with the visual transition |

**Rules:** silence is *generated as measured digital silence*, not as trailing
model output (which contains breath tails and room tone that vary). Never leave
> 2.5 s of true silence — fill with ambience or the listener thinks playback
stopped. A held image under silence is the single most powerful tool in the
audiobook format; budget at least one per act.

---

## 10. MUSIC ENGINE

`music_plan.json` per scene:

```json
{ "scene_id": "SC-014", "mood": "restrained tension", "genre": "sparse strings + low drone",
  "tempo_bpm": 62, "key_center": "D minor",
  "intensity_curve": [ { "t": 0.0, "v": 0.2 }, { "t": 0.55, "v": 0.5 }, { "t": 0.9, "v": 0.15 } ],
  "entry": "fade_in_3s", "exit": "tail_out_4s",
  "must_not": ["percussion hits", "melody competing with speech in 200–2000 Hz"] }
```

**Music laws**
1. Music enters *after* narration has established the scene, exits *before* the
   final line of the act. Wall-to-wall music deafens the audience to emphasis.
2. One cue per scene. Cue changes mid-scene only on a story turn.
3. Melody must not occupy the vocal band during narration — that is what makes
   music "loud" even at correct levels.
4. Music never ends on a hard cut unless the story does.
5. Generated only; never reproduce existing compositions (M12 §11).

---

## 11. AMBIENCE & SFX

- Ambience is continuous per location and is the *first* thing to be built —
  it hides generation seams between narration segments.
- SFX are sparse and story-motivated. Three well-placed sounds beat thirty.
- Sync tolerance: SFX within ±80 ms of the visual event, or it reads as wrong.
- Layer count ceiling: ambience 2 + SFX 3 simultaneous. More becomes noise.

---

## 12. MIX POLICY

| Element | Target (relative to narration) |
|---------|-------------------------------|
| Narration | 0 dB reference, −16 LUFS integrated |
| Dialogue | −1 to 0 dB |
| SFX | −8 to −12 dB |
| Ambience | −18 to −24 dB |
| Music (under speech) | −18 to −22 dB |
| Music (in the clear) | −8 to −12 dB |

- Sidechain duck music by 6–9 dB with 200 ms attack, 600 ms release.
- High-pass ambience and music at 80–120 Hz to keep the low end for impact.
- Narrow-Q dip in music around 2–3 kHz when speech is present (intelligibility).
- True peak ≤ −1.0 dBTP. Integrated −16 LUFS stereo (web/vertical video).
- No limiting on the narration stem before the master bus.

---

## 13. QA (audio-specific)

T1 deterministic: loudness, true peak, sample rate, channel count, DC offset,
clipping samples, silence gaps, duration vs timing map (±50 ms).

T2 model review: pronunciation of every proper noun, emotional match to
`intent`, unnatural pacing, artefacts (metallic, warbling), breath realism,
consistency with previous segments of the same speaker.

**Blocking findings:** mispronounced character name, wrong speaker, clipping,
duration mismatch > 100 ms (breaks the clock).

---

## 14. RETRY LADDER

1. `stability_adjust` (±0.10)
2. `repunctuate` — fix pacing through commas/periods, not parameters
3. `phoneme_override` — for a specific word
4. `segment_split` — long segment losing coherence
5. `voice_variant` — same identity, different take
6. escalate to M17 for a **text rewrite** — often the real fix

Voice *change* (different `voice_id`) requires human approval, always.

---

## 15. OUTPUT CONTRACT

```
assets/audio/NAR-*.wav              48 kHz / 24-bit, mono narration stems
assets/audio/DLG-*.wav              character dialogue stems
assets/audio/MUS-SC-nnn.wav         music cue per scene
assets/audio/AMB-<location>.wav     ambience beds (loopable)
assets/audio/SFX-*.wav
audio/timing_map.json               word-level timing (drives everything)
audio/pronunciation_map.json
audio/mix_report.json               levels, LUFS, ducking events
master/audio_master.wav             final mix, −16 LUFS, −1 dBTP
```

Stems are always delivered separately in addition to the mix — a video re-cut
must never require re-synthesis.

---

## 16. FAILURE MODES

| Mode | Symptom | Fix |
|------|---------|-----|
| Name roulette | Same name pronounced 3 ways | pronunciation_map, decided once |
| Concatenation seam | Audible click/room-tone jump between segments | measured silence + ambience bed |
| Emotional whiplash | Grief → cheer in one cut | one-step ladder rule (§5) |
| Speed compression | Narration sped to fit a shot | forbidden — cut words instead (LAW-3) |
| Music masking | "Can't hear the words" at correct dB | 2–3 kHz dip + vocal-band rule |
| Loudness drift | Scene 12 quieter than scene 3 | integrated LUFS per scene, not per file |
| Silence panic | Long silence sounds like a crash | ambience never fully stops |

---

## 17. ACCEPTANCE CRITERIA

- Every narration segment has a word-level timing map.
- Every proper noun appears in the pronunciation map.
- Scene-to-scene integrated loudness variance ≤ 1 LUFS.
- Stems delivered separately; master meets −16 LUFS / −1 dBTP.
- No segment's duration differs from the timeline by > 50 ms.

**NEXT MODULE:** Module 17 — AI Director

**CHANGELOG**
- v2.1 — §1c pre-generation approval gate (human must see character count +
  cost estimate and approve before any new ElevenLabs generation).
- v2.0 — Beat segmentation, acting metadata, timing map contract, silence design,
  mix targets, pronunciation governance, retry ladder.
- v1.0 — Initial outline.

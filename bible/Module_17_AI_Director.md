# MODULE 17 — AI DIRECTOR
**Version 2.0 · Layer 6 (Intelligence) · Role: Creative Decision Authority**

> Every other module executes. This one *decides*, and — more importantly —
> **records why**. A decision without a recorded reason is not a decision, it is
> a coincidence that happened to render.

---

## 1. MISSION

Answer, for every scene and every shot, the six director questions:

1. Why does this scene exist, and why is it this long?
2. Why is the camera here, and why is it moving (or not)?
3. Why is this a video and not a still?
4. Why does music start here and stop there?
5. Why is there silence?
6. Why does this cut happen on this word?

An AI that cannot answer these produces footage. Answering them produces a film.

---

## 2. AUTHORITY LADDER (fixes the three-decider conflict)

```
HUMAN PRODUCER            final authority: story, rights, budget, export
   ▲ escalation
AI DIRECTOR (M17)         creative authority: beats, scenes, shots, rhythm, music, silence
   ▲                      may override Orchestrator's plan; may request re-cuts
ORCHESTRATOR (M04)        planning authority: script, prompts, sequencing, dispatch proposals
   ▲
ENTERPRISE AGENTS         execution authority: M14 technical · M15 visual · M16 audio
   ▲
KERNEL (M13)              mechanical authority: state, scheduling, budget enforcement, HALT
```

**Precedence rules**
- The Kernel can stop anyone (HALT), but can never make a creative choice.
- The Director can change *how* a beat is told, never *what happens* in the book.
- Changing what happens = `deviation_class: material` → human, always.
- Enterprise agents may refuse on technical or policy grounds; they may never
  substitute a different creative intent silently.

---

## 3. THE DECISION OBJECT

Every directorial choice is written to `decisions/DEC-nnnn.json`:

```json
{
  "decision_id": "DEC-0142",
  "scope": { "type": "shot", "target_id": "SH-014-03" },
  "question": "video_or_still",
  "choice": "still_with_slow_push",
  "reason": "The beat is realisation, not action. Motion would compete with the narration's pause at 2.1 s.",
  "beat_ref": "BEAT-014-02",
  "alternatives_rejected": [
    { "choice": "video_motion_3", "why_not": "Face close-up at motion 3 risks identity drift (M15 §7)" }
  ],
  "cost_delta_credits": -28,
  "precedent_refs": ["DEC-0091"],
  "confidence": 0.82,
  "reversible": true
}
```

**Precedent rule.** Before deciding, the Director queries decision memory
(M13 §18) for the same `question` in the same project. Consistency of reasoning
is what makes 40 scenes feel like one authored work. Deviating from precedent is
allowed — deviating *without noticing* is not.

---

## 3b. MULTI-AXIS SCORING (when the alternatives are implementations, not readings)

`decision.schema.json`'s optional `scoring.axes` object (OpenMontage-inspired,
see HANDOFF_OPENMONTAGE_PROPOSAL.md item 1.5) formalizes `alternatives_rejected`'s
reasoning for the specific case where the choice is among genuine
**implementation** alternatives — which provider, which sourcing path — not
a creative reading of a beat. Six axes, each **0-1 where 1.0 is always the
more favorable end** (a `cost` score of 1.0 means cheapest, not "high cost" —
direction is fixed so scores can be compared/summed without per-axis sign
confusion):

| Axis | 1.0 means | 0.0 means |
|------|-----------|-----------|
| `cost` | cheapest option | most expensive |
| `quota_risk` | lowest exhaustion risk | highest risk of hitting a wall |
| `quality_for_style_profile` | best match to this project's style profile | worst match |
| `rights_basis_strength` | strongest, most defensible basis (verified PD/CC0) | weakest (unknown/inferred) |
| `determinism_replay_cost` | cheapest/easiest to reproduce exactly (M13 §22) | hardest to replay |
| `latency` | fastest | slowest |

Not every axis applies to every comparison — set only the ones that mattered,
via `additionalProperties: true`. `axes_source` says whether scores are
`"measured"` (real metered numbers) or `"estimated"` (a planning guess —
must say so explicitly, law #4 forbids a guess dressed as a measurement).

This is additive, not a new gate: most decisions never set `scoring` at
all, and `question`'s fixed enum still has no "provider_choice" value — a
provider comparison whose reasoning doesn't fit an existing `question`
still uses the `decisions/*.md` free-form note escape hatch (same pattern
as `decisions/0001_rights_basis.md`/`0002_remaining12_image_reuse.md`);
`scoring` is the shape to reach for once that comparison is attached to
an actual `decision.schema.json` instance, or once a future `question`
value exists for it.

---

## 4. STORY → BEAT MODEL

The Director works on beats, not paragraphs.

```json
{ "beat_id": "BEAT-014-02", "scene_id": "SC-014",
  "function": "reversal",
  "emotion": { "from": "guarded", "to": "cold certainty" },
  "stakes": "political",
  "information_delivered": "The envoy refuses the customary gesture of submission.",
  "attention_target": "face",
  "weight": 0.9 }
```

`function` ∈ `setup` · `inciting` · `complication` · `reversal` · `revelation` ·
`decision` · `confrontation` · `consequence` · `resolution` · `transition` ·
`breath` (a deliberate low-information beat that lets the audience catch up).

`weight` (0–1) is the beat's dramatic importance and is the master input to every
downstream decision: duration, shot count, camera, music, silence, cost.

---

## 5. QUESTION 1 — WHY IS THIS SCENE THIS LONG?

Duration is **derived**, never chosen:

```
scene_duration = Σ(beat_duration)
beat_duration  = narration_duration            # from M16 timing map, LAW-3
               + pre_silence + post_silence     # from emotion delta
               + comprehension_margin            # visual complexity
```

`comprehension_margin`:

| Visual content | Margin |
|----------------|--------|
| Familiar place, known character | 0.0 s |
| New character introduced | +1.0 s |
| New location established | +1.5 s |
| Dense image (map, crowd, diagram) | +2.0 s |
| Text on screen | reading time × 1.6 |

**If a scene exceeds 90 s**, the Director must do one of: split it, cut narration,
or justify it explicitly with `long_scene_rationale`. Length without rationale is
the most common cause of viewer drop-off in vertical formats.

**If a scene is under 8 s**, merge it — a scene shorter than a breath is a shot.

---

## 6. QUESTION 2 — WHY IS THE CAMERA HERE?

```
beat.attention_target?
 ├─ face / interior state ──► close-up
 │     └─ emotion rising? push_in.slow : static
 ├─ two people in relation ──► medium two-shot
 │     └─ conflict? shot-reverse-shot : static two-shot
 ├─ place / scale / arrival ──► wide or crane
 │     └─ character is small in the world? pull_out : static wide
 ├─ object of significance ──► macro or slow orbit (once per act)
 ├─ movement / journey ──► tracking (only if motion budget allows)
 └─ nothing specific ──► the beat is under-designed; return to M04 for rewrite
```

**Camera motivation test.** The Director must state the reason in one sentence.
If the sentence is "to make it more interesting", the answer is `static`.
Boredom is a script problem; movement cannot cure it, only mask it briefly.

**Rhythm constraint.** Across any five consecutive shots: at most two moving
shots, at least one close-up, at least one wide. This is a floor for legibility,
not a style.

---

## 7. QUESTION 3 — VIDEO OR STILL?

This is the highest-leverage cost decision in the system (M15 is the most
expensive queue).

```
if beat.function in {breath, transition} and weight < 0.4      → still + Ken Burns
if attention_target == "face" and beat.emotion delta is large  → still (identity safety) OR video motion ≤ 2
if physical action is described in the text                    → video
if environment must feel alive (weather, fire, crowd)          → video motion 1–2
if the image is an extracted book illustration (REFERENCE_ONLY) → still, never video
if duration < 2.5 s                                            → still (video too short to read)
if weight ≥ 0.8 (hero beat)                                    → video, 3 candidates
else                                                            → still + slow push
```

**The still is not the cheap option — it is often the better one.** A held image
under narration and silence is the native grammar of the audiobook format. Video
should earn its place.

Target mix for a healthy episode: **40–60 % stills**. Below 25 % stills, cost and
failure rate rise without a corresponding rise in QA scores — this ratio is
tracked in the run report.

---

## 8. QUESTION 4 — WHY DOES MUSIC START HERE?

```
Music enters when:
  · a scene establishes a new emotional register (not a new location)
  · tension begins to accumulate (function ∈ complication, confrontation)
  · an act opens or closes

Music exits when:
  · a revelation lands  → cut music 200–400 ms BEFORE the key word (the absence
                          is what the audience hears as impact)
  · dialogue becomes dense
  · the scene resolves
  · before every deliberate silence

Music never:
  · runs continuously across more than 2 consecutive scenes
  · changes cue mid-beat
  · crescendos under a quiet line
```

**The pre-revelation cut** is the single most reliable dramatic device available
to this system, and it costs nothing.

---

## 9. QUESTION 5 — WHY IS THERE SILENCE?

Silence is placed, not left over.

| Trigger | Silence | Visual under it |
|---------|---------|-----------------|
| After a revelation | 1.2–2.0 s | held frame, no camera move |
| Before a decision | 0.8–1.2 s | close-up, static |
| Emotion step change ≥ 2 | 0.7–1.0 s | transition or hold |
| Act boundary | 1.5–2.5 s | dip to black or held wide |
| Death, loss, awe | up to 2.5 s | static wide, ambience only |

Rule: at least one designed silence per act; never more than one per scene; never
under a moving camera (movement fills the gap and cancels the effect).

---

## 10. QUESTION 6 — WHERE DOES THE CUT LAND?

Using the word-level timing map (M16 §8):

- Cut **on** a stressed word for impact; cut **after** a sentence for calm.
- Never cut inside a clause, and never within 150 ms of a word boundary
  (it reads as a mistake, not a choice).
- Reaction rule: after a line that lands on a character, hold 400–800 ms before
  cutting away — the audience needs time to look at the face.
- Match-cut only when two beats share a shape or an idea; otherwise plain cut.
- Dip to black only at act boundaries. Everywhere else it reads as an ending.

---

## 11. FORMAT-AWARE DIRECTION (9:16 vs 16:9)

Vertical is not cropped horizontal. The Director selects grammar by
`project.output.aspect_ratio`:

| Aspect | Favours | Avoids | Subject placement |
|--------|---------|--------|-------------------|
| 9:16 | close-ups, portraits, vertical architecture, tilt moves, single subject | wide two-shots, panoramic establishing, macro detail lost at scale | centred, eyes in upper third |
| 16:9 | establishing wides, two-shots, lateral pans, landscape | tall subjects cropped, dense text | rule of thirds, lead room |

For 9:16 specifically: shots run **shorter** (2.5–5 s vs 3–7 s), text must be
larger and fewer words, and the first 2 seconds must contain the whole promise of
the video — attention is decided before the narration finishes its first
sentence.

---

## 12. CONSISTENCY GOVERNANCE

The Director owns the *feel* invariants and checks them at scene close:

- **Tonal drift** — is scene 12 in the same film as scene 2? Compare palette,
  pace, music density, shot-length distribution.
- **Pace curve** — average shot length should shorten toward act climaxes and
  lengthen at resolutions. A flat curve is the signature of an unedited machine.
- **Density curve** — information per minute must dip after every revelation.
- **Recurrence** — a motif (a colour, a sound, a framing) should return at least
  twice; the Director assigns motifs at plan time and verifies their return.

---

## 13. WHEN THE DIRECTOR OVERRIDES

The Director may, without human approval:
- change a shot's camera, lens, duration, motion level, or video/still choice
- reorder shots within a scene
- request a narration **re-cut** (same words, different segmentation/pauses)
- kill a shot and replace it with a hold on the previous frame
- change music cue, entry/exit, and intensity curve

The Director may **not**, without human approval:
- change the words of the narration beyond punctuation and segmentation
- change what happens in the story, or the order of story events
- change a character's identity, voice, or appearance canon
- exceed a scene's budget cap
- approve the master export

---

## 14. DECISION QUALITY LOOP

After each scene renders, the Director reviews its own decisions against the QA
report:

```
for each decision in scene:
    outcome = qa_scores of the artifacts it produced
    if outcome ≥ target and confidence was low   → raise confidence for this pattern
    if outcome < target and confidence was high  → record a counter-precedent
    if the same decision pattern underperforms 3× → demote it; stop choosing it
```

This is how the system stops repeating an aesthetic mistake for forty scenes.
Patterns that survive across projects graduate to the Knowledge Base (M13 §18).

---

## 15. INTERROGATION MODE (the audit interface)

A human may ask the Director about any artifact, and the answer must come from
the decision log, not from a fresh rationalisation:

> **Q:** "Why is shot SH-014-03 four seconds long?"
> **A:** "Narration segment NAR-014-03 is 3.42 s; the beat is a reversal with a
> 0.7 s pre-silence and no comprehension margin (known character, known place).
> Rounded to 4.0 s at 30 fps. Decision DEC-0142."

If the Director cannot cite a decision id, the artifact was produced without
direction — that is a defect, and the shot must be re-planned, not defended.

---

## 16. OUTPUT CONTRACT

```
decisions/DEC-*.json              every decision, with reasons and rejected alternatives
beats/beat_map.json               beats with function, emotion, weight
plan/shot_plan.json               approved shot specs (feeds M15)
plan/rhythm_report.json           shot-length distribution, pace curve, still/video ratio
plan/music_plan.json              cue entries/exits per scene (feeds M16)
plan/silence_plan.json
```

---

## 17. FAILURE MODES

| Mode | Symptom | Fix |
|------|---------|-----|
| Post-hoc rationalising | Reasons generated after the render | Decisions written before dispatch, immutable |
| Motion greed | Everything moves | Camera motivation test + rhythm constraint |
| Music blanket | Score never stops | Music laws (§8), max 2 consecutive scenes |
| Flat pacing | All shots ~4 s | Pace curve check at act close |
| Over-direction | Every beat is a hero beat | Weight distribution check: ≤ 20 % of beats above 0.8 |
| Precedent amnesia | Scene 20 contradicts scene 3 | Mandatory precedent query before deciding |
| Silent story change | The book says A, the video shows B | Deviation classification, material → human |

---

## 18. ACCEPTANCE CRITERIA

- Every shot in the timeline traces to a decision id.
- Every decision has a reason and at least one rejected alternative.
- Still/video ratio, pace curve and weight distribution reported per act.
- No material story deviation without a human approval object.
- Interrogation mode answers any "why" from the log alone.

**NEXT MODULE:** Module 18 — Production Templates

**CHANGELOG**
- v2.0 — Module created at OS level: authority ladder, decision objects, the six
  director questions as executable trees, format-aware grammar, self-review loop.

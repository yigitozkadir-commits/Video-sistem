# MODULE 04 — ORCHESTRATOR MASTER GUIDE
**Version 2.1 · Layer 1 (Tool Guide)**

## 1. ROLE

The Orchestrator turns a book into a *plan*: script, beats, sequencing, and
prompt assembly. It proposes; the AI Director disposes (M17 §2).

## 2. AUTHORITY

**May decide:** adaptation of prose into narration, beat segmentation, scene
ordering, prompt assembly from M19 objects, dispatch proposals.

**May not decide:** shot design, camera, music placement, gate verdicts, budget,
or anything the book does not contain.

## 3. ADAPTATION RULES

1. **Do not invent events.** Compression is allowed; invention is a material
   deviation and needs a human (M17 §13).
2. **Cut, don't rush.** If a scene runs long, remove words. Never ask the audio
   agent to speed up (LAW-3).
3. **Narration is spoken, not written.** Break long clauses; prefer concrete
   nouns; avoid parentheses and semicolons — they have no sound.
4. **One idea per sentence** at emotional peaks; complexity is for exposition.
5. **Preserve the book's names and terms verbatim**; they feed the pronunciation
   map (M16 §6).
6. Dialogue keeps its line breaks — they carry acting information.

## 4. BEAT SEGMENTATION

Emit `beat_map.json` (schema: `beat_map.schema.json`). Constraints:

- A beat is 1–4 sentences with one intention.
- `function` from the eleven-value enum; `weight` 0–1.
- At most 20% of beats may exceed weight 0.8 — if everything is a climax,
  nothing is.
- Emotion may move at most one step between adjacent beats (M16 §5), or insert a
  `breath` beat between them.

## 5. PROMPT ASSEMBLY

The Orchestrator **assembles**, never authors. It selects the active `PV-` for a
family, fills the variables, and records the resolved instance in
`prompts_used/`. Editing prompt text inline is forbidden — it destroys the
scoring signal (M19 §6).

## 6. SEQUENCING

Proposes the task graph: reference generation first (global, P1), then per scene
narration → shots → music → assembly. It may not dispatch; the kernel dispatches.

## 7. INTERACTION WITH THE DIRECTOR

The Orchestrator hands over `beat_map.json` and the script. The Director may
return `re_cut` requests (same words, different segmentation) or
`text_rewrite` requests (fewer words). Both are normal and cheap. Arguing about
shot design is not the Orchestrator's role.

## 8. OUTPUT CONTRACT

```
script/narration_script.md · beats/beat_map.json · scenes/scene_index.json
prompts_used/*.json · plan/dispatch_proposal.json
```

## 9. FAILURE MODES

| Mode | Symptom | Fix |
|------|---------|-----|
| Invention | Video shows events not in the book | Deviation classification, human gate |
| Beat inflation | 20 beats for a 30 s scene | 1–4 sentence rule, weight cap |
| Written-not-spoken prose | Narration sounds like an essay | Read-aloud test before emitting |
| Inline prompt editing | Prompt stats become meaningless | Assemble-only rule |

## 10. ACCEPTANCE CRITERIA

- Every narration line traces to source text (or to an approved deviation).
- Beat map validates and respects the weight cap.
- Zero inline-authored prompts.

**NEXT:** Module 05 — Storytelling Engine

**CHANGELOG** v2.1 — Adaptation rules, beat constraints, assemble-only prompts.

# MODULE 08 — PROMPT ENGINEERING BIBLE
**Version 2.1 · Layer 1 · Library: M19**

## 1. PRINCIPLE

A prompt is a specification, not a wish. If two people read it and imagine
different images, it is under-specified. If the model cannot fail it visibly, it
is unmeasurable.

## 2. THE FIVE RULES

1. **Structure over prose.** Fixed slots in a fixed order beat a paragraph.
2. **Front-load identity.** Early tokens dominate; put the subject first.
3. **Concrete nouns over adjectives.** "brass vessels, felt walls, cold daylight"
   beats "atmospheric, beautiful, cinematic".
4. **One instruction per slot.** Two camera moves is a defect.
5. **Negatives are a standing base**, extended per shot, never rewritten.

## 3. ANTI-PATTERNS

| Anti-pattern | Why it fails |
|--------------|--------------|
| "masterpiece, 8k, ultra detailed, trending" | Quality spam; no information, dilutes identity |
| Naming a living artist or franchise | Rights risk (M12 §11) and unstable results |
| Stacking 8 references | Model averages them into mush |
| Paragraph prompts | Untraceable, unversionable, unscoreable |
| Editing a prompt between candidates | Destroys the A/B signal |
| Writing prompts in the narration language | Prompts are English (`project.language.prompts`) |

## 4. STRUCTURED OUTPUT PROMPTS (LLM agents)

- State the schema by name and demand JSON only, no preamble, no code fences.
- Give the enum values inline; models invent categories when they aren't listed.
- Require evidence with every judgement ("cite a frame number").
- Forbid the failure you fear explicitly ("do not invent events").
- Set the refusal path: "if X is unknown, output HOLD_LEGAL" beats a guess.

## 5. TESTING A PROMPT

Same shot, same seeds, same references; change only the prompt version. Minimum
10 uses before comparing. Promote on +0.05 first-pass yield or +4 avg score at
≤ +15% cost (M19 §6).

## 6. OUTPUT CONTRACT

```
prompts/PV-*.json · prompts/axes/*.json · prompts/index.json · prompts/stats.json
```

## 7. FAILURE MODES

| Mode | Symptom | Fix |
|------|---------|-----|
| Prompt drift | Shot 30 unlike shot 1 | Assemble from slots, never edit prose |
| Quality spam | No improvement, longer prompts | Delete adjectives, add nouns |
| Untested folklore | "This phrase helps" with no data | Stats or it didn't happen |

## 8. ACCEPTANCE CRITERIA

- No prompt text exists outside `prompts/`.
- Every family has exactly one `active` version.
- Every promotion is backed by ≥ 10 measured uses.

**NEXT:** Module 09 — Asset Management & Metadata

**CHANGELOG** v2.1 — Five rules, anti-patterns, structured-output guidance, testing.

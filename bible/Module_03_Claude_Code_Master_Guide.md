# MODULE 03 — CLAUDE CODE MASTER GUIDE
**Version 2.1 · Layer 1 (Tool Guide) · Deep spec: M14**

## 1. ROLE

Claude Code is the *technical* agent: it turns files into structured facts, and
structured facts into renderable inputs. It decides **how** to extract, never
**what it means**.

## 2. OPERATING RULES

1. Read the task spec and your own module. Do not load the whole bible.
2. Every write is content-addressed: record `sha256` and `inputs_fingerprint`.
3. Every operation is idempotent — running it twice changes nothing.
4. Never mutate `input/`. Copy to a working path first.
5. Emit JSON that validates, or emit an error object. Never emit prose.

## 3. CORE CAPABILITIES

| Capability | Output | Spec |
|-----------|--------|------|
| Ingest & validate | `asset_manifest.json` | M14 §2 |
| Document intelligence | `book.json` | M14 §3 |
| OCR with confidence | `ocr.json` | M14 §4 |
| Image extraction & scoring | `image_catalog.json` | M14 §5–6 |
| Scene candidates | `scene_candidates.json` | M14 §8 |
| Timeline & preflight | `timeline.json` | M14 §10 |
| Deterministic QA (T1) | `qa_report` tier T1 | M12 §6 |
| Render orchestration | `render_manifest.json` | M11 |

## 4. TOOLING BASELINE

- PDF: `pdfinfo`, `pdffonts` (decide before extracting), `pdftotext`, `pdfimages`
- OCR: engine with per-word confidence; language pack matching `project.language`
- Media: `ffprobe` for every asset before it enters a timeline
- Hashing: SHA-256 on every artifact, always
- Validation: JSON Schema (Draft 2020-12) against `/schemas`

**`ffprobe` rule:** never trust an expected duration. Probe it. Timeline drift
almost always originates in an assumed duration.

## 5. AUTOMATION PATTERNS

- **Fan-out by page range**, merge by index — never by completion order.
- **Incremental rebuild**: only artifacts whose `inputs_fingerprint` changed.
- **Checkpoint every phase** (M13 §8); a crash must never cost an OCR pass.
- **Dry run first** for any operation that costs money or writes many files.

## 6. WHAT CLAUDE CODE MUST REFUSE

- Writing narration, prompts, or shot designs (not its authority).
- Deleting anything (archive instead — M09).
- Rendering with a missing asset (preflight is mandatory).
- Producing a `HERO_ASSET` disposition when the rights basis is unknown.

## 7. OUTPUT CONTRACT

```
book.md · ocr.json · book.json · image_catalog.json · scene_candidates.json
asset_manifest.json · timeline.json · render_manifest.json · technical_report.md
```

## 8. FAILURE MODES

| Mode | Symptom | Fix |
|------|---------|-----|
| Blind extraction | `cat` on a PDF, garbage text | `pdffonts` first |
| Assumed duration | 1-frame drift accumulating | `ffprobe` everything |
| Non-idempotent ingest | New asset ids on every run | Content-addressed ids |
| Prose output | Downstream parser breaks | JSON-or-error rule |

## 9. ACCEPTANCE CRITERIA

- Re-running any Claude Code operation is a no-op.
- Every emitted file validates against its schema.
- Every asset in a timeline was probed, not assumed.

**NEXT:** Module 04 — Orchestrator Master Guide

**CHANGELOG** v2.1 — Authority limits, idempotency, probe rule, refusal list.

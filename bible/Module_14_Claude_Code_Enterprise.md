# MODULE 14 — CLAUDE CODE ENTERPRISE
**Version 2.0 · Layer 5 (Enterprise) · Role: Technical Production Director**

> Claude Code does not "do OCR". It reads a book the way a production designer
> reads a book: what is here, what matters, what can be reused, what must be
> rebuilt, what must never be touched.

---

## 1. AUTHORITY & LIMITS

**May decide:** extraction method, image classification and scoring, asset
disposition (§7), scene *candidate* boundaries, technical feasibility, all
file/manifest operations, all deterministic QA (M12 T1).

**May not decide:** story meaning, emotional intent, shot design, final scene
boundaries, prompt creative content, anything with a rights implication.

**Escalates to:** AI Director (M17) for narrative questions, Human for `E-LEG-*`.

---

## 2. THE INGEST DECISION TREE

```
source file
 ├─ digitally authored PDF (pdffonts → fonts present)
 │    ├─ text layer clean?  ──► native extraction (fastest, most accurate)
 │    └─ text layer garbled ──► rasterize + OCR, keep native as cross-check
 ├─ scanned PDF (no fonts)
 │    ├─ ≥ 300 DPI  ──► OCR direct
 │    └─ < 300 DPI  ──► upscale pages → OCR → confidence check
 ├─ EPUB/DOCX ──► structural extraction (headings survive — use them)
 ├─ images only ──► OCR + manual chapter mapping (human confirmation required)
 └─ mixed ZIP ──► inventory, classify each member, recurse
```

**Never OCR what already has text.** Native extraction preserves reading order,
ligatures and hyphenation that OCR destroys.

Cross-check rule: if both native and OCR text exist, compute similarity. If
< 0.85, the page has a layout problem (columns, sidebars, captions) — flag
`E-OCR-202` and process that page with layout-aware extraction.

---

## 3. DOCUMENT INTELLIGENCE OUTPUT

`book.json`:

```json
{
  "title": "…", "author": "…", "language_detected": "tr",
  "pages": 212, "has_toc": true,
  "structure": [
    { "chapter": 1, "title": "…", "page_start": 7, "page_end": 21,
      "word_count": 3120, "illustration_count": 2, "confidence": 0.97 }
  ],
  "front_matter_pages": [1,2,3,4,5,6],
  "back_matter_pages": [205,206,207],
  "footnotes": [ { "page": 44, "marker": "3", "text": "…" } ],
  "extraction": { "method": "native", "ocr_fallback_pages": [88, 143],
                  "avg_confidence": 0.961 }
}
```

**Front/back matter must be separated, not deleted.** Copyright pages contain the
rights evidence M12 §11 needs.

---

## 4. OCR QUALITY POLICY

| Avg confidence | Action |
|----------------|--------|
| ≥ 0.95 | Accept |
| 0.90–0.95 | Accept; re-OCR pages below 0.85 with a second engine |
| 0.80–0.90 | Re-OCR whole document with different preprocessing (deskew, denoise, binarize) |
| < 0.80 | `E-OCR-201`, human decision: better scan or accept degraded |

**Paragraph reconstruction rules:** join hyphenated line breaks; preserve blank
lines as paragraph boundaries; never merge across a page break unless the last
line lacks terminal punctuation; keep dialogue line breaks intact (they carry
the acting information M16 needs).

**Reading-order verification:** for multi-column pages, verify by checking that
sentence-level language-model perplexity of the reconstructed order is lower than
the naive top-to-bottom order. If not, the columns were merged wrong.

---

## 5. IMAGE PIPELINE

Extract **every** embedded image plus every page region that looks like an
illustration (vector art won't be an embedded raster).

For each image record:

```json
{
  "asset_id": "AST-IMG-000041", "page": 44, "bbox": [72,180,520,640],
  "px": [1400,1180], "dpi_effective": 288, "mime": "image/png",
  "sha256": "…", "has_text_overlay": false, "is_duplicate_of": null,
  "class": "illustration", "caption_nearby": "Taidula receives the envoy",
  "scores": { "narrative_relevance": 88, "visual_quality": 62,
              "resolution_adequacy": 45, "reuse_potential": 70,
              "reference_value": 91 },
  "disposition": "reference_only",
  "rationale": "Composition and costume are canonical; resolution too low for hero use."
}
```

### 5.1 Classification taxonomy

`cover` · `illustration` · `portrait` · `map` · `diagram` · `decoration`
(ornament, drop cap, border) · `photograph` · `scan_artifact` · `blank`

Decorations and scan artifacts are cataloged and then ignored. They are never
deleted — M09's "never lose an asset" law holds.

### 5.2 Scoring rubric (0–100 each)

| Metric | 90–100 | 60–89 | < 60 |
|--------|--------|-------|------|
| `narrative_relevance` | Depicts a named story beat or main character | Depicts setting/mood | Ornamental |
| `visual_quality` | Clean, high contrast, no bleed-through | Minor noise/halftone | Heavy artifacts |
| `resolution_adequacy` | ≥ 2× target frame on short edge | 1–2× | < 1× |
| `reuse_potential` | Usable in ≥ 3 scenes | 2 scenes | single use |
| `reference_value` | Defines a character/place canon | Supports canon | none |

Scores must each cite an observation (M12 §4).

---

## 6. WHY THE SAME IMAGE GETS DIFFERENT VERDICTS

The disposition is a function of **two** things: what the image *is*, and what
the production *needs at that moment*. The same illustration can be a reference
in Act 1 and a discard in Act 3.

```
disposition(image, need) :=
  if rights_unknown                      → HOLD_LEGAL
  if reference_value ≥ 80                → REFERENCE_ONLY      (never rendered on screen)
  if narrative_relevance ≥ 75
     and resolution_adequacy ≥ 80        → HERO_ASSET          (may appear on screen)
  if narrative_relevance ≥ 75
     and resolution_adequacy 45–79       → UPSCALE_CANDIDATE
  if narrative_relevance ≥ 75
     and resolution_adequacy < 45        → REGENERATE_FROM_REFERENCE  (Flow)
  if class in {map, diagram}
     and story needs explanation         → HERO_ASSET (static, with Ken Burns)
  if class in {decoration, scan_artifact}→ ARCHIVE
  else                                   → ARCHIVE
```

### 6.1 The six dispositions

| Disposition | Meaning | Downstream |
|-------------|---------|------------|
| `REFERENCE_ONLY` | Feeds Flow's character/environment memory. Never on screen. | M15 §4 |
| `HERO_ASSET` | Appears in the final video as-is | M11 timeline |
| `UPSCALE_CANDIDATE` | Upscale, then re-score; if quality still < 70 → regenerate | M14 §8 |
| `REGENERATE_FROM_REFERENCE` | Flow generates a new image using this as reference | M15 |
| `ARCHIVE` | Kept, indexed, unused | M09 archive |
| `HOLD_LEGAL` | Blocked pending rights decision | M12 §11 |

**Hard rule:** an original illustration from a copyrighted book is
`REFERENCE_ONLY` or `HOLD_LEGAL` — never `HERO_ASSET` — unless
`project.rights.source_basis` is `public_domain` or `owned`.

---

## 7. UPSCALE POLICY

- Upscale only `UPSCALE_CANDIDATE`, never speculatively (cost, M13 §21).
- Max 4× factor. Beyond that, hallucination exceeds fidelity — regenerate instead.
- Re-score after upscale on `visual_quality` and `resolution_adequacy` only.
  If `visual_quality` **dropped** (plastic skin, smeared text), reject the upscale
  and keep the original as reference.
- Text inside an image must remain legible after upscale, or the upscale fails.

---

## 8. SCENE DISCOVERY (candidates, not decisions)

Claude Code proposes scene boundaries; M17 approves them.

**Boundary signals** (weighted vote, threshold 0.6):

| Signal | Weight | Detection |
|--------|--------|-----------|
| Explicit break (chapter, `***`, blank block) | 0.45 | structural |
| Location change | 0.20 | NER + place lexicon |
| Time jump | 0.15 | temporal expressions |
| Character set change | 0.10 | entity set diff > 50 % |
| Illustration anchor | 0.05 | image on page |
| Emotional turn | 0.05 | sentiment delta > 0.4 |

**Length constraints:** target 20–90 s of narration per scene (M10 §7). A
candidate implying > 120 s must be split at the strongest internal signal; one
implying < 8 s must be merged with a neighbour. Report both actions as
`scene_adjustment` findings — M17 may override.

Output: `scene_candidates.json` with `confidence` and `signals_fired` per
boundary. Never overwrite `scene_index.json` — that is the Orchestrator's file
(M13 §5).

---

## 9. TEXT → PRODUCTION ARTIFACTS

Claude Code produces the *technical* layer only:

```
book.md                  # clean reading text, chapter-anchored
ocr.json                 # per-page text + confidence + bbox
image_catalog.json       # every image with scores and disposition
scene_candidates.json    # proposed boundaries with evidence
asset_manifest.json      # everything on disk, hashed
dependency_graph.json    # seed graph (M13 §7)
technical_report.md      # human-readable summary of what was found
```

It must **not** produce: narration text, prompts, shot designs, emotional maps.

---

## 10. REMOTION PREPARATION

Claude Code owns the mechanical translation of an approved storyboard into
Remotion input:

- `timeline.json` — absolute frame numbers, derived from narration audio
  (LAW-3). Every entry: `{ start_frame, end_frame, layer, asset_id, transform }`
- `composition.json` — fps, dimensions, durationInFrames, safe areas
- `captions.srt` / `.ass` — from the narration timing map (M16), never re-typed
- Preflight: every referenced asset exists, resolves, decodes, and has the
  expected duration. A render started with a missing asset is `E-REN-703` and is
  always a preflight bug, never a Remotion bug.

**Frame math rule:** all durations convert to frames once, at this boundary,
with `round(seconds * fps)`. Downstream never sees seconds. Mixed units are the
main source of one-frame drift across a long video.

---

## 11. AUTOMATION & INCREMENTAL BUILDS

- Everything is content-addressed: `inputs_fingerprint` (M13 §8) decides rebuild.
- Parallel extraction by page range; merge by page index, never by completion order.
- A rebuild after a text edit must touch only the scenes containing that text.
  If it touches more, the dependency graph is wrong — fix the graph, not the build.
- Idempotency: running ingest twice on the same source produces identical
  manifests and zero new asset IDs.

---

## 12. CLAUDE CODE AS REVIEWER

Claude Code runs all of M12 Tier 1 and may run Tier 2 for *structural* artifacts
(timelines, manifests, captions). It may **never** T2-review a generative
artifact it requested, and may never review visual aesthetics — that is the
Review Agent's job with vision capability.

---

## 13. LOGGING

Per operation: `operation, input_hashes, output_hashes, duration_ms, pages_touched,
warnings[], errors[], tool_versions{}`. Tool versions matter: an OCR engine
upgrade changes output and must invalidate fingerprints.

---

## 14. FAILURE MODES

| Mode | Symptom | Response |
|------|---------|----------|
| Silent OCR degradation | Confidence fine, text nonsense (wrong language model) | Language detect per page, not per book |
| Illustration duplication | Same art extracted 5× (repeated ornament) | Perceptual hash dedupe, keep one, link the rest |
| Column merge | Sentences interleaved | Reading-order verification (§4) |
| Over-extraction | 900 "images" from a 200-page book | Filter: area < 0.5 % of page and no caption → decoration |
| Scene explosion | 400 scene candidates | Enforce length constraints (§8) before emitting |
| Fingerprint omission | Cache serves stale assets | Fingerprint is mandatory on every write |

---

## 15. ACCEPTANCE CRITERIA

- Every page has a confidence score; every image has a disposition and rationale.
- No `HERO_ASSET` exists without a rights basis recorded.
- Scene candidates carry evidence, not assertions.
- Re-running ingest is a no-op.
- Timeline preflight passes before any render task is dispatched.

**NEXT MODULE:** Module 15 — Flow Enterprise

**CHANGELOG**
- v2.0 — Decision trees for extraction and image disposition, scoring rubrics,
  scene-candidate voting model, frame-math rule, rights gating.
- v1.0 — Initial outline.

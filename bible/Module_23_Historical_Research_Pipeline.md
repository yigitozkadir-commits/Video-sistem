# MODULE 23 — HISTORICAL RESEARCH PIPELINE
**Version 1.0 · Layer 0 (Pre-production) · Role: Research Director**

> Every other project so far has started from a `.docx`/`.pdf` the human
> already researched and handed over. This module is what happens when
> nobody has written that document yet — it originates one, under the same
> 8 laws that govern everything downstream of it.

## 1. ROLE

Executable as `.claude/skills/historical-research-pipeline/` (Skill tool:
`historical-research-pipeline`). Runs a 5-phase, source-grounded historical
research process — Discovery → Deep Research → Verification → Synthesis &
Audit → Production Package — and stops. It never writes narration, scenes,
or prompts; those are M05/M08/M17's job, starting from this module's
output.

Adapted from a 29-module concept document, consolidated to 5 phases
without losing capability (overlapping modules — e.g. three separate
"find more sources" modules — collapsed into one phase each does once).
Full phase instructions: `.claude/skills/historical-research-pipeline/phases/faz-{a,b,c,d,e}-*.md`.
Shared record shapes (Claim/Evidence/Source/Unknown/Angle/Hook):
`.claude/skills/historical-research-pipeline/reference/sema.md`. Formal
output contract: `schemas/research_package.schema.json`.

## 2. AUTHORITY

**May decide:** which sources are admissible, claim decomposition,
confidence/verdict levels, historiographical framing, content-angle and
hook selection, the READY/CONDITIONAL/BLOCKED readiness verdict.

**May not decide:** the eventual video's narration text, shot design, or
emotional intent (M05/M17 own those) — this module's output ends at a
research package, never a script. It also may not silently promote a
`SPECULATION`/`MYTH`-tagged item to fact-equivalent status anywhere in its
own output; that boundary is enforced inside the pipeline itself (Phase C
verdicts, Phase D's completeness audit), not by a downstream reviewer.

## 3. THE 8 LAWS, APPLIED HERE

1. **Contract over prose** — `schemas/research_package.schema.json` is the
   real gate; a Phase E package that doesn't validate isn't done, however
   good the prose reads.
2. **Single writer** — this module owns `research/<slug>/`. Nothing else
   in the studio writes there, and it never writes into an existing
   `projects/<id>/` path except via the explicit §4 bridge below.
3. **Narration is the clock** — N/A at this stage (no audio exists yet);
   the discipline this module enforces instead is "evidence is the
   clock" — a claim's confidence level is set by what was found, not by
   how good the resulting story would be.
4. **No silent degradation** — `UNKNOWN`/`SOURCE_GAP`/`CONTESTED` are
   valid, first-class outputs, not failures to paper over. A source that
   can't be reached after all of Phase B3b's fallback steps is marked
   `SOURCE_GAP` with `attempted_access_methods` recorded, never silently
   dropped from the bibliography.
5. **Deterministic replay** — every claim carries `confidence_history`
   (append-only — Phase B's draft value is never overwritten, only
   superseded with a reason at each phase); every source carries
   `url_or_locator` and enough metadata to re-find it. "Why is this
   ESTABLISHED" must be answerable from the record alone, same test as
   `studio why` (CLAUDE.md §8).
6. **Cost is a constraint** — Phase B's saturation rule (stop expanding
   once new searches repeat existing findings) is this module's budget
   discipline; there is no dollar cost to track here (WebSearch/WebFetch
   are the only tools used — see §6), but there is a time/attention
   budget, and the orchestration's "progress update every 10-15
   searches" norm exists so a long run stays legible.
7. **Human gates are explicit objects** — Phase D5's Readiness Gate
   (`BLOCKED | CONDITIONAL | READY | HIGH_CONFIDENCE_READY`) is reported
   to the human explicitly; Phase E never runs on a `BLOCKED` verdict
   without the human choosing to proceed anyway.
8. **Fail loud, resume cheap** — each phase's output is written to disk
   (`research/<slug>/faz-*.json`) before the next phase starts, so a
   session that runs out of turns/context resumes from the last
   completed phase file instead of re-researching from scratch.

## 4. BRIDGE — FROM RESEARCH PACKAGE TO PROJECT SOURCE

Every existing project in this studio began with
`project.json.source.file` pointing at a human-supplied document. This
module lets that document be `research/<slug>/faz-e-package.md` instead.
The bridge is **opt-in** (Phase E delivers a standalone package first;
converting it into a new project is a separate, explicit step — see
`.claude/skills/historical-research-pipeline/phases/faz-e-uretim-paketi.md`'s
final orchestration note):

1. Copy `faz-e-package.md` into the new project's `input/` directory.
2. Compute its `sha256`, fill `project.json.source.file`/`sha256`.
3. Set `rights.source_basis: "owned"` (this studio's own synthesis of
   cited public sources — same category `PRJ-ninniler-atlasi` used for
   its own academic compilation, see `decisions/0001_rights_basis.md`'s
   pattern in that project).
4. Set `rights.evidence_ref` to point at the package's `bibliography`
   field — the evidence for "owned" here IS the citation trail, not an
   external license.
5. From here on, this is a normal project: the usual
   `scripts/scaffold_<project>_project.py` pattern takes over. No
   scaffold script currently reads a `faz-e-package.json` structurally
   (e.g. auto-generating `scenes/SC-*.json` from its `claims`/`chronology`
   fields) — that is a natural next automation once a real project has
   gone through this bridge once, deliberately not built speculatively
   ahead of a real use (same discipline as M11 §5b's documented scope
   decision).

## 5. THE 5 PHASES (summary — full instructions in phase files)

| Phase | Question it answers | Output file | Gate? |
|---|---|---|---|
| A — Discovery & Concept | What's actually worth researching here? | `faz-a-concept.json` | Scope-width gate (A1b): too broad → split into candidates, ask human |
| B — Deep Research | What does the evidence say, from every channel (web/academic/primary-source-chain/multilingual/material)? | `faz-b-dossier.json` | Saturation (B4) — stop expanding, not a human gate |
| C — Verification & Analysis | Does the evidence actually survive an adversarial attack on it? | `faz-c-verification.json` | None — feeds D |
| D — Synthesis & Audit | Is this actually ready to hand off? | `faz-d-master-dossier.json` + `faz-d-readiness.json` | **D5 Readiness Gate — hard stop on BLOCKED** |
| E — Production Package | What's the strongest, evidence-backed angle to build from? | `faz-e-package.json` + `.md` | Handoff Contract (schema-validated) |

## 6. TOOLS / ACCESS

No paid API key is required. The pipeline runs entirely on Claude Code's
built-in `WebSearch`, `WebFetch`, and `AskUserQuestion` tools — all
already available in this environment.

**Optional, not required:**
- **Semantic Scholar API key** (free tier — https://www.semanticscholar.org/product/api)
  raises Phase B3.2's academic-literature search rate limit versus plain
  `WebSearch`/`WebFetch` queries against `api.semanticscholar.org`. The
  pipeline works without it — degrades to `WebSearch`-based scholarly
  queries (`site:scholar.google.com` etc., already in the phase file).
- **CrossRef API** — free, no key needed at all (optionally a contact
  email in the request for CrossRef's "polite pool", still no key).
- **Wayback Machine / Internet Archive** — free, no key, and this studio
  already depends on the same public API elsewhere
  (`scripts/find_reference_images.py`'s `archive_org` provider, M09 §8b) —
  no new setup.
- A dedicated academic-search MCP server (if one is added to this Claude
  Code account's marketplace later) could replace the `WebSearch`-based
  academic workaround in Phase B3.2 with structured results. Not assumed
  present — check `SearchMcpRegistry` if this becomes worth adding later,
  not a current dependency of this module.

## 7. FAILURE MODES

| Symptom | Cause | First move |
|---|---|---|
| Confident claim, thin sourcing | Phase C1's adversarial pass skipped or shallow | Re-run C1 fully before trusting `confidence` |
| Package delivered but `BLOCKED` ignored | Orchestration skipped the D5 human-report step | Never let E run silently after a BLOCKED verdict |
| Source silently dropped | Phase B3b's fallback ladder not followed to completion | Mark `SOURCE_GAP` with `attempted_access_methods`, never omit |
| One-sided history on a contested topic | C2's `perspective_diversity` check skipped | Re-run C2, search the underrepresented side's literature explicitly |
| Direct long quote from a source | E3's paraphrase discipline (15-word quote cap) not enforced | Rewrite in the pipeline's own words, keep only a short verbatim fragment if any |

## 8. ACCEPTANCE CRITERIA

- `faz-e-package.json` validates against `schemas/research_package.schema.json`.
- Every `core`/`supporting` claim has a non-empty `confidence_history` and
  at least one linked source.
- The D5 readiness verdict was reported to the human before Phase E ran.
- No claim's `type` is `speculation` or `interpretation` while its
  `confidence` implies `ESTABLISHED`/`STRONGLY_SUPPORTED` — the epistemic
  label and the claim type must not contradict each other.
- If the §4 bridge was used, the resulting project's `rights.evidence_ref`
  actually resolves to the package's `bibliography`, not left generic.

**NEXT MODULE:** none yet — this is the newest module. Its natural
successor, if built, is a scaffold script that consumes
`faz-e-package.json` structurally (see §4 point 5).

**CHANGELOG**
- v1.0 — Module created: adapted from an uploaded 29-module concept
  document (packaged as a Claude skill) into this studio's 5-phase
  pipeline, schema (`schemas/research_package.schema.json`), and the
  bridge into `project.json.source` (§4). See
  `HANDOFF_OPENMONTAGE_PROPOSAL.md`-adjacent session work for the
  broader context this module was added alongside.

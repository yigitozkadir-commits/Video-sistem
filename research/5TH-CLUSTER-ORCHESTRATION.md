# 5th Cluster Orchestration — Items 201-400

## Cluster Composition (200 items, 5 sections)

| Section | Items | Count | Focus |
|---------|-------|-------|-------|
| DAMGALAR | 201-240 | 40 | Turkic clan marks, symbols, proto-writing |
| ATASÖZLERI | 241-270 | 30 | Proverbs, folk wisdom, moral philosophy |
| İSİMLER | 271-310 | 40 | Naming traditions, etymology, meanings |
| SEMBOLLER | 311-350 | 40 | Shared symbols, pre-Islamic markers |
| DÜNYA-HALKLAR | 351-400 | 50 | Diaspora communities, modern identities |

---

## Phase Pipeline (Continuous, No Breaks)

### Phase A: Concept Cards (In Progress)
- Agent: a1512dbb492080aa8
- Sections: 5 (DAMGALAR → ATASÖZLERI → İSİMLER → SEMBOLLER → DÜNYA-HALKLAR)
- Output: 5 × concept-a-*.json (angle selection + scoring)
- ETA: ~1-1.5 hours

**→ ON A COMPLETION, TRIGGER FAZ B+C**

---

### Phase B+C: Deep Research + Verification (Queued)
**Trigger Condition:** Faz A complete
- Parallel agents: 5 (one per section)
- Task: Web research (Gemini) + Red Team Mode (adversarial verification)
- Output: 5 × faz-b-dossier-*.json + 5 × faz-c-verification-*.json
- Sources target: 20+ per section (100+ total)
- Claims target: 50-60 unique claims
- ETA: ~2-3 hours per section (parallel)

**→ ON B+C COMPLETION, TRIGGER FAZ D**

---

### Phase D: Synthesis + Quality Gate (Queued)
**Trigger Condition:** Faz B+C complete
- Parallel agents: 5 (one per section)
- Task: Consolidate B+C → Evidence graphs + Causal chains
- Output: 5 × faz-d-master-dossier-*.json + 5 × faz-d-readiness-*.json
- Readiness verdicts: READY / CONDITIONAL / BLOCKED
- ETA: ~1-2 hours per section (parallel)

**→ ON D COMPLETION, TRIGGER FAZ E**

---

### Phase E: Production Packages (Queued)
**Trigger Condition:** Faz D complete
- Single agent: 1 (master orchestrator)
- Task: E1 (angle) + E2 (hook) + E3 (package) + E4 (manifest)
- Output: 5 × faz-e-package-*.json + FAZ-E-MASTER-MANIFEST
- ETA: ~1 hour

---

## Total Timeline

- Faz A: 1-1.5h
- Faz B+C: 2-3h (parallel)
- Faz D: 1-2h (parallel)
- Faz E: 1h
- **TOTAL: 5-7.5 hours (non-stop)**

---

## Gemini + NVIDIA API Usage

**Faz B (Research):**
- Per-section: ~30 web searches (Gemini real-time search)
- Per-claim: 2-3 academic sources (Gemini synthesis)
- Total: ~150-200 API calls across 5 sections

**Faz C (Verification):**
- Per-claim: Red Team Mode (Gemini adversarial prompt)
- Per-section: Historiography audit (Gemini multi-perspective analysis)
- Total: ~100-150 API calls across 5 sections

**Faz D (Synthesis):**
- Per-section: NVIDIA NIM vectorization (optional, for claim clustering)
- Total: ~50 embedding operations

**Faz E (Packaging):**
- Minimal API calls (mostly local JSON formatting)

**Cost:** Gemini free tier should cover; NVIDIA free credits buffer

---

## Success Criteria

- ✅ Faz A: 5/5 sections with primary angles selected
- ✅ Faz B: 100+ independent sources across 5 sections
- ✅ Faz C: 7+ red-team flags per section, historiography audit documented
- ✅ Faz D: 5 readiness verdicts (goal: 4 READY, 1 CONDITIONAL max)
- ✅ Faz E: 5 production packages + master manifest
- ✅ No API failures or rate limits
- ✅ All outputs committed to git

---

## Monitoring

Each phase completion:
1. Verify output files exist
2. Commit to git
3. Trigger next phase agent
4. Report progress

**Note:** Do not stop between phases. Continuous pipeline until Faz E complete.


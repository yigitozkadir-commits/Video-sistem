# 5th Cluster Resume Plan — Session Limit Recovery

## What Happened

5 Faz B+C agents hit session limit (infrastructure rate-limit, not API keys):
- Reset time: 11:20am UTC
- Progress: Substantial (research + claims identified, but Faz B/C dossiers incomplete)

## Agent Status Before Limit

| Section | Agent ID | Progress | Next Step |
|---------|----------|----------|-----------|
| DAMGALAR | aed99738bf1891c10 | 35+ sources, 12 claims | Compile Faz B dossier JSON |
| ATASÖZLERI | a61937d62853932ee | Faz B research complete | Generate Faz C verification |
| İSİMLER | a7284cf983077ddd8 | Claims mapped | Create Faz C JSON |
| SEMBOLLER | ac06b58e9ca623438 | 12 claims identified | Compile Faz B JSON |
| DIASPORA | a8cf979987bc86291 | Phase B research done | Format Phase B dossier |

## Resume Strategy (After 11:20am UTC Reset)

### For Each Agent:
1. SendMessage to resume with checkpoint context
2. Instruct to complete:
   - Faz B dossier JSON (if not done)
   - Faz C verification JSON (if not done)
   - Output to `research/5th-cluster-kesif/` directory
3. No re-research needed (already have 35+ sources per section)
4. Focus on: structuring claims, evidence mapping, JSON output

### Resume Prompts:

**DAMGALAR (aed99738bf1891c10):**
```
You found 35+ sources and 12 claims before session limit. Now:
1. Compile Faz B dossier: structure 12 claims with evidence/sources
2. Generate Faz C verification: Red Team Mode analysis
3. Output: faz-b-dossier-damgalar.json + faz-c-verification-damgalar.json
Devam et!
```

**ATASÖZLERI (a61937d62853932ee):**
```
Faz B research complete. Continue:
1. Generate Faz C verification JSON (Red Team Mode)
2. Output: faz-c-verification-atasozleri.json
Devam et!
```

Similar for others...

## Timeline After Reset

- **11:20am UTC:** Session limit resets
- **11:20am+5m:** Resume all 5 agents in parallel
- **11:20am+1h:** Expect completion (just JSON compilation, no new research)
- **11:20am+1.5h:** Auto-trigger Faz D (5 parallel synthesis agents)
- **11:20am+3h:** Auto-trigger Faz E (production packages)

---

## Success Criteria

- ✅ 5 × faz-b-dossier-*.json (research summarized)
- ✅ 5 × faz-c-verification-*.json (red team audit)
- ✅ All files valid JSON
- ✅ Commit to git

---

## If Resume Fails

Fallback: Spawn fresh Faz B+C agents starting from Faz A outputs (concept cards already done). Will re-research but guaranteed completion.


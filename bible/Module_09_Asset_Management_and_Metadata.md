# MODULE 09 — ASSET MANAGEMENT & METADATA SYSTEM
**Version 2.1 · Layer 2 (Data)**

## 1. LAWS

Never lose an asset. Never overwrite an original. Every asset has an id, a hash,
metadata, a creator and a provenance chain. Deletion does not exist — only
archiving.

## 2. LIFECYCLE

`Ingest → Validate → Catalog → Metadata → QA → Version → Store → Reuse → Archive`

## 3. IDENTIFIERS

`AST-<TYPE>-<nnnnnn>` where TYPE ∈ IMG, VID, AUD, TXT, JSN, SUB. Allocated by the
kernel from `state/id_registry.json`. **Ids are never reused**, even after
archiving. Full registry: M13 §11.

## 4. REQUIRED METADATA

`asset_id, asset_type, path, mime_type, sha256, bytes, created_at, creator_agent,
scene_reference, shot_reference, version, disposition` — plus for generated
assets: `model, model_version, seed, prompt_version`.

An asset without generation provenance cannot be replayed and violates LAW-5.

## 5. HASHING & DEDUPLICATION

SHA-256 on every artifact. Perceptual hash additionally on images, to catch the
same ornament extracted forty times. Duplicates are linked (`is_duplicate_of`),
not deleted.

## 6. VERSIONING

`major.minor.patch` per artifact family. A new version is a new file and a new
id. The manifest records the chain; the timeline references exactly one version.

## 7. CACHE & INVALIDATION

The **only** invalidation rule is `inputs_fingerprint` (M13 §8): hash of spec +
references + prompt version + model + seed. Editing an unrelated scene never
invalidates yours. Time-based expiry does not exist here.

## 8. REFERENCE ASSETS

Immutable. Used for character, environment, object and palette consistency.
Regeneration produces a new `REF-` id; existing shots keep the old one, so
history stays reproducible.

## 9. DEPENDENCY TRACING

Every asset records its inputs. `studio why <asset>` walks: asset → task →
prompt version → decision → beat → source page. Any break in that chain is a
defect.

## 10. OUTPUT CONTRACT

```
asset_manifest.json · scene_manifest.json · render_manifest.json
dependency_graph.json · archive/ (immutable, hashed)
```

## 11. FAILURE MODES

| Mode | Symptom | Fix |
|------|---------|-----|
| Orphan assets | Files nobody references | Manifest sweep at scene close |
| Broken chain | Cannot explain an asset | Provenance fields mandatory |
| Silent overwrite | Old version gone | Write-new-id discipline |
| Duplicate storm | 900 images from 200 pages | Perceptual dedupe + decoration filter |

## 12. ACCEPTANCE CRITERIA

- 100% of assets hashed and cataloged.
- 0 orphans and 0 dangling references at every gate.
- Every generated asset replays from its recorded provenance.

**NEXT:** Module 10 — Scene Management & Storyboard

**CHANGELOG** v2.1 — Fingerprint-only invalidation, provenance requirements, tracing.

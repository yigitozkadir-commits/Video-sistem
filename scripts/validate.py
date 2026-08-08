#!/usr/bin/env python3
"""Validate the Studio OS repository: JSON well-formedness, schema coverage,
cross-references, and (if jsonschema is installed) instance validation."""
import json, os, sys, glob

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
errors, warnings = [], []


def load(path):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception as e:
        errors.append(f"{os.path.relpath(path, ROOT)}: invalid JSON — {e}")
        return None


def main():
    # 1. every JSON parses
    files = glob.glob(f"{ROOT}/**/*.json", recursive=True)
    objs = {f: load(f) for f in files}
    print(f"parsed {len(files)} JSON files")

    # 2. schemas present
    schemas = {os.path.basename(p): objs[p] for p in files if "/schemas/" in p}
    print(f"schemas: {len(schemas)}")
    for required in ["project.schema.json", "task.schema.json", "qa_report.schema.json",
                     "envelope.schema.json", "shot.schema.json", "decision.schema.json"]:
        if required not in schemas:
            errors.append(f"missing core schema: {required}")

    # 3. bible modules present
    mods = sorted(glob.glob(f"{ROOT}/bible/Module_*.md"))
    print(f"bible modules: {len(mods)}")
    nums = {int(os.path.basename(m).split("_")[1]) for m in mods}
    for n in range(1, 23):
        if n not in nums:
            errors.append(f"missing bible module {n:02d}")

    # 4. every module has the house sections
    for m in mods:
        text = open(m).read()
        for section in ["ACCEPTANCE CRITERIA", "CHANGELOG"]:
            if section not in text.upper():
                warnings.append(f"{os.path.basename(m)}: no {section} section")

    # 5. templates reference existing style profiles
    for p in glob.glob(f"{ROOT}/templates/*.json"):
        t = objs.get(p) or {}
        ref = (t.get("visual") or {}).get("style_profile_ref", "")
        if ref and not ref.endswith("inherit.json"):
            if not os.path.exists(os.path.join(ROOT, ref)):
                errors.append(f"{os.path.basename(p)}: style_profile_ref not found: {ref}")
        ex = t.get("extends")
        if ex and not os.path.exists(f"{ROOT}/templates/{ex}.json"):
            errors.append(f"{os.path.basename(p)}: extends unknown template {ex}")
        # qa_overrides may only tighten (M18 §4)
        gates = (t.get("qa_overrides") or {}).get("gates", {})
        for gate, cfg in gates.items():
            base = {"shot_accept": 75, "scene_accept": 78, "master_export": 82}.get(gate)
            if base and cfg.get("min_weighted", base) < base:
                errors.append(f"{os.path.basename(p)}: loosens gate {gate} (forbidden)")

    # 6. prompt index points at existing active prompts
    idx = objs.get(f"{ROOT}/prompts/index.json") or {}
    for family, entry in (idx.get("families") or {}).items():
        pid = entry.get("active")
        if not os.path.exists(f"{ROOT}/prompts/{pid}.json"):
            errors.append(f"prompts/index.json: {family} -> missing {pid}")
    # exactly one active per family
    seen = {}
    for p in glob.glob(f"{ROOT}/prompts/PV-*.json"):
        o = objs.get(p) or {}
        if o.get("status") == "active":
            seen.setdefault(o.get("family"), []).append(o.get("prompt_id"))
    for fam, ids in seen.items():
        if len(ids) > 1:
            errors.append(f"family {fam} has {len(ids)} active prompts: {ids}")

    # 7. optional: instance validation
    try:
        from jsonschema import Draft202012Validator
        pairs = [("projects/project.example.json", "project.schema.json"),
                 ("studio.config.json", None)]
        for inst, sch in pairs:
            if sch is None:
                continue
            ip, sp = f"{ROOT}/{inst}", f"{ROOT}/schemas/{sch}"
            if os.path.exists(ip) and os.path.exists(sp):
                v = Draft202012Validator(json.load(open(sp)))
                for e in v.iter_errors(json.load(open(ip))):
                    errors.append(f"{inst}: {e.message}")
        for p in glob.glob(f"{ROOT}/templates/*.json"):
            v = Draft202012Validator(json.load(open(f"{ROOT}/schemas/template.schema.json")))
            for e in v.iter_errors(json.load(open(p))):
                errors.append(f"{os.path.relpath(p, ROOT)}: {e.message}")
        for p in glob.glob(f"{ROOT}/prompts/PV-*.json"):
            v = Draft202012Validator(json.load(open(f"{ROOT}/schemas/prompt.schema.json")))
            for e in v.iter_errors(json.load(open(p))):
                errors.append(f"{os.path.relpath(p, ROOT)}: {e.message}")
        print("instance validation: on (jsonschema installed)")
    except ImportError:
        warnings.append("jsonschema not installed — instance validation skipped "
                        "(pip install jsonschema)")

    print()
    for wmsg in warnings:
        print(f"WARN  {wmsg}")
    for e in errors:
        print(f"ERROR {e}")
    print()
    if errors:
        print(f"FAILED — {len(errors)} error(s), {len(warnings)} warning(s)")
        return 1
    print(f"OK — 0 errors, {len(warnings)} warning(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

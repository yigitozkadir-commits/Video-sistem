#!/usr/bin/env python3
"""
Reads every projects/<id>/state/cost_ledger.jsonl and
render_manifest.jsonl in the repo and prints a summary: this is the
"Monitoring"/"Metrics" item from the optimization docs made concrete -
a report you can actually run, not a dashboard that doesn't exist yet.

Usage:
    python3 scripts/production_report.py
"""
import glob
import json
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def main():
    print("=" * 72)
    print("PRODUCTION REPORT")
    print("=" * 72)

    for state_dir in sorted(glob.glob(str(REPO_ROOT / "projects" / "*" / "state"))):
        project = Path(state_dir).parent.name
        ledger = load_jsonl(Path(state_dir) / "cost_ledger.jsonl")
        manifests = load_jsonl(Path(state_dir) / "render_manifest.jsonl")
        errors = load_jsonl(Path(state_dir) / "errors.jsonl")

        if not ledger and not manifests and not errors:
            continue

        print(f"\n### {project}")

        if ledger:
            by_provider = defaultdict(lambda: {"calls": 0, "hits": 0, "units": 0.0,
                                                "failed": 0, "duration_sum": 0.0, "duration_n": 0})
            for row in ledger:
                p = by_provider[row["provider"]]
                p["calls"] += 1
                if row["operation"].endswith("_cache_hit"):
                    p["hits"] += 1
                if not row["accepted"]:
                    p["failed"] += 1
                p["units"] += row.get("units", 0) or 0
                if row.get("duration_s") is not None:
                    p["duration_sum"] += row["duration_s"]
                    p["duration_n"] += 1

            print("  Cost ledger:")
            for provider, stats in by_provider.items():
                hit_rate = stats["hits"] / stats["calls"] * 100 if stats["calls"] else 0
                avg_latency = (stats["duration_sum"] / stats["duration_n"]) if stats["duration_n"] else None
                latency_str = f", {avg_latency:.1f}s avg latency" if avg_latency is not None else ""
                print(f"    {provider}: {stats['calls']} calls, "
                      f"{stats['hits']} cache hits ({hit_rate:.0f}%), "
                      f"{stats['failed']} failed, "
                      f"{stats['units']:.0f} units consumed{latency_str}")

        if manifests:
            total_bytes = sum(o["bytes"] for m in manifests for o in m.get("outputs", []))
            succeeded = sum(1 for m in manifests if m["result"] == "success")
            print(f"  Renders: {len(manifests)} total, {succeeded} succeeded, "
                  f"{total_bytes / 1_000_000:.1f} MB total output")
            for m in manifests:
                out = m["outputs"][0] if m["outputs"] else {}
                print(f"    - {m['target_id']}: {m['result']}, "
                      f"{m['resolution']}@{m['fps']}fps, "
                      f"{out.get('bytes', 0) / 1_000_000:.1f} MB, "
                      f"sha256={out.get('sha256', '?')[:12]}...")

        if errors:
            needs_human = [e for e in errors if e.get("escalate_to") == "human"]
            print(f"  Errors: {len(errors)} total, {len(needs_human)} need human action")
            for e in needs_human:
                print(f"    ACTION NEEDED [{e['code']}] {e['error_id']}: {e['message']}")
                if e.get("suggested_strategy"):
                    print(f"      -> {e['suggested_strategy']}")

    print()


if __name__ == "__main__":
    main()

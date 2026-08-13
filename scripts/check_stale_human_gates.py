#!/usr/bin/env python3
"""
Detects stale human approval gates - bible/Module_13 §15 documents the
approval object lifecycle and §10's D3 failure mode ("Task in
BLOCKED(awaiting_approval) > approval_sla -> notify human, apply
on_timeout policy"), and studio.config.json's human block already carries
approval_sla_hours/on_timeout, but until now nothing in the codebase ever
checked a pending approval's age against that SLA - a documented-but-
unimplemented gap (confirmed via grep: zero scripts referenced approvals
before this one, and per Module_13's own note, zero approval.schema.json
instances have ever actually been created in this repo).

Scope, deliberately: this script DETECTS and REPORTS staleness. It does not
itself execute the on_timeout policy (hold/proceed_p3/abort) - deciding to
abort a project or unblock downstream work is a production decision this
script has no authority over (CLAUDE.md §3: "You may never decide... gate
verdicts on generative artifacts"). It prints which policy applies so a
human or the orchestrator can act on it. This mirrors pre_render_checklist
scripts' advisory contract: a finding must be reviewed and consciously
handled, never silently skipped (CLAUDE.md law #4), but the script itself
never blocks or mutates anything.

Storage convention: one JSON-lines file per project at
projects/<id>/state/approvals.jsonl, each line an approval.schema.json
object. approval.schema.json has no requested_at/created_at field (a
confirmed gap - only decided_at and expires_at exist, both meaningless for
a still-pending approval) - this script reads requested_at via the
schema's additionalProperties:true escape hatch. A pending record with no
requested_at cannot have its age computed; per law #4 that is itself
reported as a finding (a data-quality gap), never silently treated as
"not stale".

Usage:
    python3 scripts/check_stale_human_gates.py
Exit code 0 = no stale/malformed pending gates found, 1 = findings need
review (does not block anything by itself - see Scope above).
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
PROJECTS_DIR = REPO_ROOT / "projects"
CONFIG_PATH = REPO_ROOT / "studio.config.json"


def _human_config() -> dict:
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text()).get("human", {})
    return {}


def _parse_iso(ts: str):
    # approval_id/requested_at etc. use date-time format per schema
    # (RFC 3339) - Python's fromisoformat wants "+00:00" not a bare "Z".
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def _iter_approval_records():
    """Yields (project_id, approvals_path, line_no, record) for every line
    in every projects/PRJ-*/state/approvals.jsonl found. Malformed JSON
    lines are reported as findings by the caller, not raised here."""
    for approvals_path in sorted(PROJECTS_DIR.glob("PRJ-*/state/approvals.jsonl")):
        project_id = approvals_path.parent.parent.name
        for line_no, line in enumerate(approvals_path.read_text().splitlines(), start=1):
            line = line.strip()
            if not line:
                continue
            yield project_id, approvals_path, line_no, line


def check_stale_human_gates() -> list[str]:
    cfg = _human_config()
    sla_hours = cfg.get("approval_sla_hours", 24)
    on_timeout = cfg.get("on_timeout", "hold")
    now = datetime.now(timezone.utc)

    findings = []
    for project_id, approvals_path, line_no, raw_line in _iter_approval_records():
        rel = approvals_path.relative_to(PROJECTS_DIR.parent)
        try:
            record = json.loads(raw_line)
        except json.JSONDecodeError as e:
            findings.append(f"{rel}:{line_no}: malformed JSON, cannot check staleness ({e})")
            continue

        if record.get("decision") != "pending" or record.get("revoked"):
            continue

        approval_id = record.get("approval_id", f"<no approval_id, line {line_no}>")
        requested_at = record.get("requested_at")
        if not requested_at:
            findings.append(
                f"{project_id} {approval_id}: pending approval has no requested_at - "
                f"cannot compute staleness (add requested_at when the approval is created)"
            )
            continue

        try:
            requested_dt = _parse_iso(requested_at)
        except ValueError:
            findings.append(
                f"{project_id} {approval_id}: requested_at {requested_at!r} is not a valid "
                f"ISO 8601 timestamp, cannot compute staleness"
            )
            continue

        age_hours = (now - requested_dt).total_seconds() / 3600.0
        if age_hours > sla_hours:
            scope = record.get("scope", {})
            findings.append(
                f"{project_id} {approval_id}: pending {age_hours:.1f}h "
                f"(SLA {sla_hours}h) on scope {scope.get('type', '?')}:"
                f"{scope.get('target_id', '?')} - on_timeout policy is {on_timeout!r}, "
                f"apply it (or renew requested_at after human follow-up)"
            )

    return findings


def main():
    findings = check_stale_human_gates()
    if not findings:
        print("Stale human gate check: clean. 0 findings.")
        sys.exit(0)

    print(f"Stale human gate check: {len(findings)} finding(s) - review:\n")
    for f in findings:
        print(f"  - {f}")
    sys.exit(1)


if __name__ == "__main__":
    main()

"""
Writes schemas/error.schema.json-compliant records to state/errors.jsonl.

This is the real-world scope of the "Retry Intelligence" / "Dead Letter
Queue" idea from the uploaded Sandrex architecture docs: those docs describe
a distributed queue service with its own DLQ topic. This repo has no queue
service - it has scripts/lib/retry.py, which already retries and gives up.
The gap wasn't infrastructure, it was that giving up left no record. This
module is that record, in the shape the studio bible already defines
(error.schema.json), so `production_report.py` and a human answering
CLAUDE.md's "studio why" test can see what failed permanently without
re-reading logs.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))
from lib.id_counter import next_id  # noqa: E402


def _error_id(state_dir: Path) -> str:
    n = next_id(state_dir / ".error_counter")
    return f"ERR-{n:05d}"


def log_error(
    project_state_dir: Path,
    code: str,
    message: str,
    retryable: bool,
    task_ref: Optional[str] = None,
    attempt: Optional[int] = None,
    evidence: Optional[dict] = None,
    escalate_to: Optional[str] = None,
    suggested_strategy: Optional[str] = None,
) -> dict:
    """Append one error.schema.json record to state/errors.jsonl and return it."""
    state_dir = Path(project_state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)
    row = {
        "error_id": _error_id(state_dir),
        "code": code,
        "retryable": retryable,
        "message": message,
        "occurred_at": datetime.now(timezone.utc).isoformat(),
    }
    if task_ref:
        row["task_ref"] = task_ref
    if attempt is not None:
        row["attempt"] = attempt
    if evidence:
        row["evidence"] = evidence
    if escalate_to:
        row["escalate_to"] = escalate_to
    if suggested_strategy:
        row["suggested_strategy"] = suggested_strategy
    with open(state_dir / "errors.jsonl", "a") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row

"""
Shared, lock-protected monotonic counter for ID allocation.

Module 13 Section 11 says: "IDs are immutable and never reused. Counters
live in state/id_registry.json and are allocated by the kernel only." The
two real counters in this repo (errors.py's ERR-nnnnn, production_ledger.py's
TSK-nnnnnn) used to each do their own unlocked read -> increment -> write
against a plain counter file. studio.config.json's concurrency block
(q.qa: 6, q.visual: 3, ...) means multiple workers can legitimately run at
once, and an unlocked read-modify-write under real concurrency is exactly
how two tasks end up allocated the same ID, or an increment gets lost - a
direct violation of "never reused". fcntl.flock blocks the second writer
until the first finishes its read-modify-write, which is enough for a
single-machine multi-process studio (this repo has no distributed workers).
"""
from __future__ import annotations

import fcntl
from pathlib import Path


def next_id(counter_file: Path) -> int:
    """Read-increment-write counter_file under an exclusive lock, return
    the new value. Creates the file (starting at 1) if it doesn't exist."""
    counter_file.parent.mkdir(parents=True, exist_ok=True)
    # Open in r+ if the file exists, else create it - a single fixed mode
    # ("a+") that supports both, then seek to 0 to read from the start.
    with open(counter_file, "a+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            f.seek(0)
            raw = f.read().strip()
            n = int(raw) + 1 if raw else 1
            f.seek(0)
            f.truncate()
            f.write(str(n))
            f.flush()
            return n
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)

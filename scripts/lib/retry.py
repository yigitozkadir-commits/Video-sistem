"""
Retry-with-backoff, reading the retry contract that studio.config.json
already defines (retry.transient_max, backoff_base_s, backoff_cap_s,
jitter) but that nothing in the codebase actually implemented until now.

CLAUDE.md law #6 ("Cost is a constraint — budget exhaustion halts
production") means quota/budget errors must NOT be retried - retrying a
401 quota_exceeded just wastes more calls against a wall that won't move.
Only genuinely transient failures (network errors, 5xx, timeouts) should
back off and retry. Callers mark which category applies by raising
`NonRetryable` for anything that retrying can't fix.
"""
from __future__ import annotations

import json
import random
import time
from pathlib import Path
from typing import Callable, TypeVar

T = TypeVar("T")

_CONFIG_PATH = Path(__file__).parent.parent.parent / "studio.config.json"


class NonRetryable(Exception):
    """Raise this (or a subclass) from inside a retried function to signal
    the failure is not transient - e.g. quota exhaustion, validation
    failure, auth error. with_retry() will not retry these; it re-raises
    immediately."""


class WallClockExceeded(Exception):
    """Cumulative with_retry() loop time (attempts + backoff so far)
    exceeded studio.config.json's timeouts.<queue> ceiling in minutes.

    This bounds the retry LOOP, not a single fn() call - a call that hangs
    with no timeout of its own (e.g. a subprocess) is not interrupted by
    this; that needs its own timeout at the call site (CLAUDE.md law #4:
    be honest about what a mitigation does and doesn't cover)."""


def _retry_config() -> dict:
    if _CONFIG_PATH.exists():
        return json.loads(_CONFIG_PATH.read_text()).get("retry", {})
    return {}


def _timeout_config() -> dict:
    if _CONFIG_PATH.exists():
        cfg = json.loads(_CONFIG_PATH.read_text()).get("timeouts", {})
        return {k: v for k, v in cfg.items() if k != "_comment"}
    return {}


def with_retry(
    fn: Callable[[], T],
    category: str = "transient",
    on_retry: Callable[[int, Exception], None] | None = None,
    error_context: dict | None = None,
    queue: str | None = None,
) -> T:
    """Call fn() with exponential backoff + jitter on transient failure.

    category selects the max-attempts key from studio.config.json's retry
    block: "transient" -> transient_max, "generation" -> generation_max,
    "validation" -> validation_max, "compliance" -> compliance_max (0 by
    design - compliance failures never auto-retry).

    queue, if given (one of the "q.*" keys studio.config.json's timeouts
    block shares with concurrency), adds a wall-clock ceiling on top of the
    attempt-count check above: cumulative time since with_retry() was
    called (attempts + backoff sleeps) is checked at the top of each loop
    iteration, and WallClockExceeded is raised if it has passed the
    configured minutes - this is a distinct failure mode from "attempts
    exhausted", for genuinely runaway operations (e.g. a transient error
    with a long backoff cap looping past a sane ceiling). Omit queue to
    keep the old attempts-only behavior unchanged.

    error_context, if given, is a dict with "project_state_dir" plus two
    codes (E-<CLASS>-nnn strings per schemas/error.schema.json): "code" for
    the "attempts exhausted, still transient" case and "nonretryable_code"
    for the NonRetryable case (they're usually different classes - e.g.
    E-GEN-001 for exhausted network retries vs E-BUD-001 for a quota wall).
    "timeout_code" is the equivalent for WallClockExceeded, defaulting to
    E-SYS-221 (error.schema.json has no dedicated timeout class; mapped
    under E-SYS per the SYS class's general "system-level failure" scope).
    "task_ref" and "escalate_to" are optional. When the call ultimately
    fails, a schema-compliant error record is appended to state/errors.jsonl
    before the exception propagates. Omit error_context to keep the old
    fire-and-forget behavior unchanged.
    """
    cfg = _retry_config()
    max_attempts = cfg.get(f"{category}_max", 3)
    base = cfg.get("backoff_base_s", 5)
    cap = cfg.get("backoff_cap_s", 600)
    jitter = cfg.get("jitter", 0.2)

    timeout_s = None
    if queue is not None:
        minutes = _timeout_config().get(queue)
        if minutes is not None:
            timeout_s = minutes * 60
    start = time.monotonic()

    attempt = 0
    while True:
        attempt += 1
        if timeout_s is not None and (time.monotonic() - start) > timeout_s:
            exc = WallClockExceeded(
                f"queue {queue!r} exceeded wall-clock ceiling of {timeout_s}s "
                f"after {attempt - 1} completed attempt(s)"
            )
            if error_context:
                _log_final_error(error_context, exc, attempt - 1, retryable=False,
                                  code=error_context.get("timeout_code", "E-SYS-221"))
            raise exc
        try:
            return fn()
        except NonRetryable as e:
            if error_context:
                _log_final_error(error_context, e, attempt, retryable=False,
                                  code=error_context.get("nonretryable_code", error_context.get("code")))
            raise
        except Exception as e:
            if attempt >= max_attempts:
                if error_context:
                    _log_final_error(error_context, e, attempt, retryable=True,
                                      code=error_context.get("code"))
                raise
            delay = min(cap, base * (2 ** (attempt - 1)))
            delay *= 1 + random.uniform(-jitter, jitter)
            if on_retry:
                on_retry(attempt, e)
            time.sleep(max(0, delay))


def _log_final_error(error_context: dict, exc: Exception, attempt: int, retryable: bool, code: str) -> None:
    # local import: avoids a hard dependency for callers that never pass
    # error_context. Uses the lib.<module> convention (scripts/ on
    # sys.path) - relies on whatever imported lib.retry having already
    # added scripts/ to sys.path, same as every other lib.* import here.
    from lib.errors import log_error

    log_error(
        project_state_dir=error_context["project_state_dir"],
        code=code,
        message=str(exc),
        retryable=retryable,
        task_ref=error_context.get("task_ref"),
        attempt=attempt,
        escalate_to=error_context.get("escalate_to", "human" if not retryable else "director"),
        suggested_strategy=error_context.get("suggested_strategy"),
    )

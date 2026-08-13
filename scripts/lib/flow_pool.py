"""
Bookkeeping for the free-tier Google Flow account pool
(schemas/flow_account_pool.schema.json).

Review finding B-07: the schema was fully specified (10 accounts, 3
videos/account/day, 10s/clip -> 300s/day pool cap - studio.config.json's
flow_account_pool block) but nothing read or wrote it. This module is pure
bookkeeping, not automation: this repo has no Flow API client (see
scripts/README.md section 8 - Flow generation happens in the Flow web UI,
by a human, using prompts Claude Code writes). What was actually missing
was an answer to "which of my 10 accounts should I paste this prompt into
next, and has it already hit today's cap" without the human tracking it by
memory. next_available_account() answers the first question,
record_usage() the second, reset_if_new_day() handles the daily quota
reset Google enforces on their side.

Never invents accounts: init_new() requires the human's real account_id/
email list. There is no default account roster, the same "never guess"
posture CLAUDE.md takes on rights_basis (section 4).
"""
from __future__ import annotations

import fcntl
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

DAILY_VIDEO_CAP = 3
MAX_CLIP_SECONDS = 10
# Fixed design capacity of the full 10-account pool (studio.config.json's
# flow_account_pool.daily_video_seconds_cap, also schemas/
# flow_account_pool.schema.json's pool_totals.daily_video_seconds_cap
# const:300) - NOT derived from how many accounts happen to be registered
# right now. A partially-populated pool (e.g. 3 real accounts so far)
# still reports against this fixed reference cap, same as the config file
# does; it's the pool's designed ceiling, not a live account tally.
DAILY_VIDEO_SECONDS_CAP = 300


class FlowPoolNotInitialized(Exception):
    """Raised by next_available_account()/record_usage() when no pool
    state file exists yet. Call FlowAccountPool.init_new() once with the
    human's real account list - never auto-created with placeholder data."""


class FlowAccountPool:
    def __init__(self, project_state_dir: Path, pool_file: str = "flow_account_pool.json"):
        self.state_dir = Path(project_state_dir)
        self.path = self.state_dir / pool_file

    def _load(self) -> Optional[dict]:
        if not self.path.exists():
            return None
        return json.loads(self.path.read_text())

    def _save(self, data: dict) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        # Lock across the whole load-modify-save call sites (see each
        # public method) rather than just this write, so two concurrent
        # callers can't both read the same pre-update state and clobber
        # each other's change - same class of bug as B-01's ID counters.
        with open(self.path, "a+") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                f.seek(0)
                f.truncate()
                f.write(json.dumps(data, indent=2, ensure_ascii=False))
                f.flush()
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)

    def init_new(self, accounts: list[dict], pool_id: str = "POOL-flow-01") -> dict:
        """accounts: list of {"account_id": "FLWACC-01", "email": "..."},
        the human's real accounts. Overwrites any existing pool state for
        this project - call this once, not per-run."""
        if not accounts:
            raise ValueError("init_new() requires at least one real account - refusing to invent one")
        now = datetime.now(timezone.utc)
        reset_at = (now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)).isoformat()
        data = {
            "pool_id": pool_id,
            "accounts": [
                {
                    "account_id": a["account_id"],
                    # email/last_used_at are typed as plain "string" in the
                    # schema (no null variant, unlike quarantine_reason) -
                    # omit them entirely rather than writing null when unset.
                    **({"email": a["email"]} if a.get("email") else {}),
                    "tier": "free",
                    "daily_video_cap": DAILY_VIDEO_CAP,
                    "max_clip_seconds": MAX_CLIP_SECONDS,
                    "videos_used_today": 0,
                    "seconds_reserved_today": 0.0,
                    "images_used_today": 0,
                    "state": "ACTIVE",
                    "reset_at": reset_at,
                    "quarantine_reason": None,
                }
                for a in accounts
            ],
        }
        self._recompute_totals(data)
        self._save(data)
        return data

    def _require(self) -> dict:
        data = self._load()
        if data is None:
            raise FlowPoolNotInitialized(
                f"No pool state at {self.path} - call FlowAccountPool.init_new() with your real "
                "Flow accounts first (see scripts/lib/flow_pool.py docstring)."
            )
        return data

    @staticmethod
    def _recompute_totals(data: dict) -> None:
        accounts = data["accounts"]
        active = [a for a in accounts if a["state"] == "ACTIVE"]
        reserved = sum(a.get("seconds_reserved_today", 0.0) for a in accounts)
        totals = {
            "daily_video_seconds_cap": DAILY_VIDEO_SECONDS_CAP,
            "seconds_reserved_today": reserved,
            "seconds_remaining_today": max(0.0, DAILY_VIDEO_SECONDS_CAP - reserved),
            "images_unlimited": True,
            "active_accounts": len(active),
        }
        # total_accounts has schema const:10 - only emit it once the pool
        # is actually fully populated, rather than reporting a wrong count
        # while it's still being built out account-by-account.
        if len(accounts) == 10:
            totals["total_accounts"] = 10
        data["pool_totals"] = totals

    def reset_if_new_day(self) -> bool:
        """Google resets each account's daily cap on its own 24h cycle
        (reset_at). Call this before next_available_account() so a stale
        EXHAUSTED account from yesterday doesn't get skipped today.
        Returns True if any account was reset. QUARANTINED accounts are
        NOT auto-reset - that's a human-reviewed state (rate-limit/abuse
        pattern), not a daily quota."""
        data = self._require()
        now = datetime.now(timezone.utc)
        changed = False
        for a in data["accounts"]:
            reset_at = datetime.fromisoformat(a["reset_at"])
            if now >= reset_at:
                a["videos_used_today"] = 0
                a["seconds_reserved_today"] = 0.0
                a["images_used_today"] = 0
                a["reset_at"] = (now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)).isoformat()
                if a["state"] == "EXHAUSTED":
                    a["state"] = "ACTIVE"
                changed = True
        if changed:
            self._recompute_totals(data)
            self._save(data)
        return changed

    def next_available_account(self) -> Optional[dict]:
        """Least-loaded ACTIVE account (fewest videos_used_today), tied
        broken by least-recently-used - spreads wear across the pool
        instead of hammering account #1 until it's exhausted. Returns None
        if every account is ACTIVE-but-full or non-ACTIVE (caller should
        fall back to still per studio.config.json's
        flow_account_pool.fallback_to_still)."""
        data = self._require()
        candidates = [a for a in data["accounts"] if a["state"] == "ACTIVE" and a["videos_used_today"] < a["daily_video_cap"]]
        if not candidates:
            return None
        candidates.sort(key=lambda a: (a["videos_used_today"], a.get("last_used_at") or ""))
        return candidates[0]

    def record_usage(self, account_id: str, video_seconds: Optional[float] = None, is_image: bool = False) -> dict:
        """Record one generation against account_id. Pass video_seconds
        for a video clip (increments videos_used_today +
        seconds_reserved_today, flips to EXHAUSTED at daily_video_cap) or
        is_image=True for a still (images_used_today only - unlimited per
        schema, no cap check)."""
        data = self._require()
        for a in data["accounts"]:
            if a["account_id"] == account_id:
                account = a
                break
        else:
            raise ValueError(f"unknown account_id {account_id!r} - not in this pool")

        account["last_used_at"] = datetime.now(timezone.utc).isoformat()
        if is_image:
            account["images_used_today"] += 1
        if video_seconds is not None:
            account["videos_used_today"] += 1
            account["seconds_reserved_today"] += video_seconds
            if account["videos_used_today"] >= account["daily_video_cap"]:
                account["state"] = "EXHAUSTED"

        self._recompute_totals(data)
        self._save(data)
        return account

    def quarantine(self, account_id: str, reason: str) -> dict:
        """Human/QA-driven: mark an account QUARANTINED (rate-limit ban,
        error pattern, ToS concern). Does not auto-clear on reset_if_new_day -
        a human must reinstate it explicitly by editing the state file or
        adding a reinstate() call once there's a real need for one."""
        data = self._require()
        for a in data["accounts"]:
            if a["account_id"] == account_id:
                a["state"] = "QUARANTINED"
                a["quarantine_reason"] = reason
                self._recompute_totals(data)
                self._save(data)
                return a
        raise ValueError(f"unknown account_id {account_id!r} - not in this pool")

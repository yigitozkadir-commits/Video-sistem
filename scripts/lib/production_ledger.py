"""
Concrete implementations of two ideas from the uploaded optimization docs,
scoped to what this repo actually does (PDF -> crop -> ElevenLabs narration
-> Remotion render) and built against schemas the studio bible already
defines (schemas/cost_ledger.schema.json, schemas/render_manifest.schema.json) -
not new invented formats.

ArtifactCache: content-addressed cache for generated narration. Hashes the
exact inputs that determine ElevenLabs output (text, voice, model, voice
settings). Re-running a generator script with the same inputs reuses the
existing file instead of calling the API again - this is what "artifact
fingerprinting" and "cache-first execution" mean when they're not just
words on a slide.

CostLedger: append-only JSONL log of every provider call, in
cost_ledger.schema.json shape, plus a running per-provider unit total this
process can check *before* making a call. This exists because this
project hit ElevenLabs' free-tier character quota three separate times
mid-batch across the Gök Umay Atlas videos - each time discovered only
after a failed API call. A pre-flight check against a known quota ceiling
turns that into a warning before the call, not a 401 after it.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))
from lib.id_counter import next_id  # noqa: E402


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("RUN-%Y%m%dT%H%MZ")


def _task_id(project_state_dir: Path) -> str:
    """Monotonic per-project task counter, formatted TSK-NNNNNN."""
    n = next_id(project_state_dir / ".task_counter")
    return f"TSK-{n:06d}"


class ArtifactCache:
    """Content-addressed cache keyed by a fingerprint of the generation inputs.

    index_name lets independent artifact types (narration audio, rendered
    scene clips, ...) keep separate cache indexes in the same state dir
    instead of colliding on one file."""

    def __init__(self, project_state_dir: Path, index_name: str = "audio_cache_index.json"):
        self.state_dir = Path(project_state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.state_dir / index_name
        self._index = json.loads(self.index_path.read_text()) if self.index_path.exists() else {}

    @staticmethod
    def fingerprint(**inputs) -> str:
        """sha256 over the sorted, canonical inputs that determine the output."""
        canonical = json.dumps(inputs, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def get(self, fp: str) -> Optional[Path]:
        entry = self._index.get(fp)
        if not entry:
            return None
        p = Path(entry["path"])
        if not p.exists():
            return None  # cached record is stale; caller should regenerate
        return p

    def put(self, fp: str, output_path: Path, **metadata) -> None:
        self._index[fp] = {
            "path": str(output_path),
            "sha256": _sha256_file(output_path),
            "cached_at": datetime.now(timezone.utc).isoformat(),
            **metadata,
        }
        self.index_path.write_text(json.dumps(self._index, indent=2, ensure_ascii=False))

    def reuse(self, fp: str, dest_path: Path) -> bool:
        """If a cache hit exists, copy it to dest_path and return True."""
        hit = self.get(fp)
        if hit is None:
            return False
        if hit.resolve() != Path(dest_path).resolve():
            shutil.copy(hit, dest_path)
        return True


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class CostLedger:
    """Append-only cost log, schemas/cost_ledger.schema.json shape.
    Also tracks a running per-provider unit total so callers can check
    remaining budget before making a call, not just after it fails.
    """

    def __init__(self, project_state_dir: Path, known_quota_units: dict | None = None):
        self.state_dir = Path(project_state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.ledger_path = self.state_dir / "cost_ledger.jsonl"
        self.run_id = _run_id()
        # e.g. {"elevenlabs": 10000} - free-tier character quota per key.
        # Purely local bookkeeping; the real limit lives at the provider.
        self.known_quota_units = known_quota_units or {}

    def units_used(self, provider: str, operation_prefix: Optional[str] = None) -> float:
        """operation_prefix narrows the sum to operations starting with it
        (e.g. "tts_") - schemas/cost_ledger.schema.json's provider enum has
        no "elevenlabs_music" vs "elevenlabs_tts" distinction, only 5
        generic providers, so two cost types sharing "elevenlabs" (chars
        for narration vs seconds for music) would otherwise sum into one
        meaningless total and corrupt each other's quota check. Omit for
        the old whole-provider behavior."""
        if not self.ledger_path.exists():
            return 0.0
        total = 0.0
        for line in self.ledger_path.read_text().splitlines():
            row = json.loads(line)
            if row.get("provider") != provider or not row.get("accepted"):
                continue
            if operation_prefix and not row.get("operation", "").startswith(operation_prefix):
                continue
            total += row.get("units", 0) or 0
        return total

    def would_exceed_quota(self, provider: str, additional_units: float, operation_prefix: Optional[str] = None) -> bool:
        """Also use this for a whole batch up front: sum the units every
        item in the batch will need and call this once before looping,
        rather than discovering the wall on item 5 of 9."""
        cap = self.known_quota_units.get(provider)
        if cap is None:
            return False
        return self.units_used(provider, operation_prefix=operation_prefix) + additional_units > cap

    def log(self, provider: str, operation: str, units: float, unit_cost: float,
            accepted: bool, scene_id: str | None = None, duration_s: float | None = None) -> None:
        row = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "run_id": self.run_id,
            "task_id": _task_id(self.state_dir),
            "provider": provider,
            "operation": operation,
            "units": units,
            "unit_cost": unit_cost,
            "cost": round(units * unit_cost, 6),
            "attempt": 1,
            "accepted": accepted,
        }
        if scene_id:
            row["scene_id"] = scene_id
        if duration_s is not None:
            row["duration_s"] = round(duration_s, 3)
        with open(self.ledger_path, "a") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

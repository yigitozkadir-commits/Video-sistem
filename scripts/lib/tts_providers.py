"""
TTSProvider: the minimal shared shape ElevenLabsStudio (scripts/
elevenlabs_client.py) already implements and PiperClient (scripts/
piper_client.py) implements the same way, so a caller can hold either
behind one name.

Why this exists (OpenMontage-inspired, see HANDOFF_OPENMONTAGE_PROPOSAL.md
item 1.4): ElevenLabs quota exhaustion has hit this studio mid-batch three
separate times (production_ledger.py's own docstring), and the studio was
literally started with zero API keys configured (this session's first
message). Until now there was no second TTS path at all - a quota wall
meant a hard stop. Piper (local, free, no network) fills that gap, but
ONLY as a draft-quality stand-in: CLAUDE.md law #4 ("no silent
degradation") means a robotic local voice must never quietly become the
final master. quality_gate marks that explicitly on every provider, and
select_tts_provider() only ever falls back with a printed/logged notice,
never silently.

This is intentionally NOT an abstract base class with enforced method
overrides - ElevenLabsStudio already exists, is tested, and duck-types
into this shape without modification (CLAUDE.md law #2, single writer:
elevenlabs_client.py owns its own file, this module doesn't reach in and
change it). TTSProvider below is documentation of the shape, not enforced
inheritance.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Protocol

REPO_ROOT = Path(__file__).parent.parent.parent
_CONFIG_PATH = REPO_ROOT / "studio.config.json"


class TTSProvider(Protocol):
    """Shape both ElevenLabsStudio.text_to_speech() and
    PiperClient.text_to_speech() already satisfy: same positional/keyword
    contract, same metadata dict shape back (scene_id, file, model,
    status, ...). quality_gate is a class attribute, not a method."""

    quality_gate: str  # "final" or "draft_only"

    def text_to_speech(self, text: str, scene_id: str, output_path: Path, **kwargs) -> dict: ...


def _project_state_dir(output_path: Path) -> Path:
    """projects/<id>/assets/audio/x.wav -> projects/<id>/state/ - same
    convention as elevenlabs_client.py's own copy (kept separate, not
    imported, so this fallback path has no import-time dependency on the
    elevenlabs SDK being installed at all)."""
    parts = output_path.resolve().parts
    if "projects" in parts and "assets" in parts:
        proj_idx = parts.index("projects")
        project_root = Path(*parts[: proj_idx + 2])
        return project_root / "state"
    return output_path.parent.parent / "state"


def _narration_fallback_config() -> dict:
    if _CONFIG_PATH.exists():
        return json.loads(_CONFIG_PATH.read_text()).get("narration", {}).get("fallback", {})
    return {}


def select_tts_provider(reason: str | None = None):
    """Returns an ElevenLabsStudio instance, or - only if
    studio.config.json's narration.fallback.enabled is true AND
    ElevenLabsStudio failed to initialize (missing SDK or missing
    ELEVENLABS_API_KEY) - a PiperClient instance instead.

    reason, if given, is logged with the fallback notice (e.g. "quota
    exhausted mid-batch") for callers that already know why they're
    falling back rather than just probing at startup.

    Raises whatever ElevenLabsStudio's own __init__ raised if fallback is
    disabled or unavailable - never silently returns nothing (law #4)."""
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from elevenlabs_client import ElevenLabsStudio  # noqa: E402

    try:
        return ElevenLabsStudio()
    except Exception as primary_exc:
        cfg = _narration_fallback_config()
        if not cfg.get("enabled"):
            raise
        from piper_client import PiperClient  # noqa: E402

        print(
            f"NOTE: ElevenLabs unavailable ({primary_exc}) - falling back to Piper "
            f"(quality_gate=draft_only, narration.fallback.enabled=true in "
            f"studio.config.json).{' Reason: ' + reason if reason else ''}",
            file=sys.stderr,
        )
        return PiperClient()

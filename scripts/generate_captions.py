#!/usr/bin/env python3
"""
Generates a schemas/caption_track.schema.json-compliant per-scene caption
file from measured narration audio, via faster-whisper's word-level
timestamps. Two consumers share this one transcription instead of running
faster-whisper twice for two different purposes: remotion_template's
StudioComposition.tsx (burned-in captions via @remotion/captions - review
finding B-05) and CLAUDE.md section 10's long-compound-number listen-check
(lib/checklist_common.long_compound_number_findings uses the same source
text a human would otherwise transcribe by ear).

faster-whisper is an optional dependency (requirements.txt keeps it
commented out - it pulls a real ML model file on first use, not something
every install needs). This script raises a clear pip-install message
rather than a bare ImportError traceback if it's missing.

Re-running with the same audio file + model + language is a no-op
(CLAUDE.md hard rule): the output's inputs_fingerprint is checked BEFORE
invoking the (expensive) transcription, not after.

Usage:
    python3 scripts/generate_captions.py SC-001 \
        projects/PRJ-x/assets/audio/NAR-SC-001.wav \
        projects/PRJ-x/state/captions/SC-001.json \
        [--model base] [--language tr] [--force]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))
from lib.production_ledger import _sha256_file  # noqa: E402

try:
    from faster_whisper import WhisperModel
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False


class FasterWhisperNotInstalled(ImportError):
    pass


def _fingerprint(audio_sha256: str, model_name: str, language: str) -> str:
    canonical = json.dumps(
        {"audio_sha256": audio_sha256, "model": model_name, "language": language},
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def transcribe_words(audio_path: Path, model_name: str, language: str) -> tuple[list[dict], str]:
    """Runs faster-whisper with word_timestamps=True. Returns
    (captions, detected_language) where captions is already shaped as
    @remotion/captions' Caption[] (text/startMs/endMs/timestampMs/
    confidence - field names and nullability verified against
    remotion-dev/remotion's packages/captions/src/caption.ts).
    timestampMs is always null: faster-whisper's Word type (start, end,
    word, probability) has no equivalent field - null is the honest value,
    not a fabricated one (CLAUDE.md law #4)."""
    if not FASTER_WHISPER_AVAILABLE:
        raise FasterWhisperNotInstalled(
            "faster-whisper not installed - it's an optional dependency (see "
            "requirements.txt). Install with: pip install faster-whisper"
        )
    model = WhisperModel(model_name)
    segments, info = model.transcribe(str(audio_path), word_timestamps=True, language=language or None)

    captions = []
    for segment in segments:
        for word in (segment.words or []):
            captions.append({
                "text": word.word,
                "startMs": round(word.start * 1000),
                "endMs": round(word.end * 1000),
                "timestampMs": None,
                "confidence": round(word.probability, 4),
            })
    detected_language = language or getattr(info, "language", None) or "unknown"
    return captions, detected_language


def generate_captions(
    scene_id: str,
    audio_path: Path,
    output_path: Path,
    model_name: str = "base",
    language: str = "tr",
    force: bool = False,
) -> dict:
    """Orchestrates the no-op-if-unchanged check, then transcribe_words(),
    then writes output_path. Returns the written dict either way (cached
    or freshly transcribed)."""
    if not audio_path.exists():
        raise FileNotFoundError(f"audio file not found: {audio_path}")

    audio_sha256 = _sha256_file(audio_path)
    fp = _fingerprint(audio_sha256, model_name, language)

    if not force and output_path.exists():
        try:
            existing = json.loads(output_path.read_text())
        except (json.JSONDecodeError, OSError):
            existing = {}
        if existing.get("inputs_fingerprint") == fp:
            return existing

    captions, detected_language = transcribe_words(audio_path, model_name, language)
    # Fingerprint is keyed on the *requested* language (what determines
    # transcription behavior), not whatever faster-whisper auto-detected -
    # recompute isn't needed since language was already known going in.
    data = {
        "scene_id": scene_id,
        "source_audio": str(audio_path),
        "model": f"faster-whisper-{model_name}",
        "language": detected_language,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs_fingerprint": fp,
        "captions": captions,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    return data


def main(argv: Optional[list[str]] = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("scene_id")
    parser.add_argument("audio_path", type=Path)
    parser.add_argument("output_path", type=Path)
    parser.add_argument("--model", default="base", help="faster-whisper model name (default: base)")
    parser.add_argument("--language", default="tr", help="language code (default: tr)")
    parser.add_argument("--force", action="store_true", help="re-transcribe even if inputs are unchanged")
    args = parser.parse_args(argv)

    data = generate_captions(
        args.scene_id, args.audio_path, args.output_path,
        model_name=args.model, language=args.language, force=args.force,
    )
    print(f"{len(data['captions'])} words -> {args.output_path}")


if __name__ == "__main__":
    main()

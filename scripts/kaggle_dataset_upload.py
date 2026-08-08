#!/usr/bin/env python3
"""
Safe, generic "add or replace one file in a Kaggle dataset" - extracted
from archive_to_kaggle.py's already-correct pattern (that script only
targets mehmetkync16/studio-large-source-assets; this one takes the
dataset ref as an argument so any project's delivery step can use it).

Written 2026-08-08 after `kaggle datasets version -p <dir>` was run by hand
against mehmetkync16/ai-audiobook-studio-videos with a directory containing
ONLY the new file - Kaggle's versioning REPLACES the dataset's entire file
list with whatever is in <dir>, it does not merge/append across calls. That
dropped 6 existing files (3 of this studio's own master videos, recovered
from local output/; 4 files with no local copy, not recoverable from this
session). archive_to_kaggle.py's docstring already documented this exact
gotcha - this incident happened because that script was scoped narrowly
and its pattern wasn't reused for a video-dataset upload. This script is
the fix: always download the dataset's current file list first, add the
new/changed file to that local copy, and re-upload everything together.
Never call `kaggle datasets version` directly for a shared dataset.

Recovery note (2026-08-08): if this mistake happens anyway, don't assume
dropped files are gone - Kaggle keeps prior dataset versions unless
`--delete-old-versions` was passed (this script never passes it). The
`kaggle` CLI itself has no way to fetch an old version, but the Kaggle MCP
tools' `list_dataset_files`/`download_dataset` both accept a
`datasetVersionNumber`. Scan version numbers (they don't reset per-dataset,
so try a range) until one lists the missing file(s), then use
`download_dataset` to get a signed GCS URL and `curl` it down. All 4 files
dropped by this exact incident were fully recovered this way from version 5.

Usage:
    python3 scripts/kaggle_dataset_upload.py <owner/dataset-slug> \
        <local_file_path> <kaggle_filename> [--message "..."]
"""
import argparse
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent


def dataset_files() -> dict[str, int]:
    """{filename: size_bytes} from the dataset's CURRENT file listing -
    the actual server state, not an assumption."""
    out = subprocess.run(["kaggle", "datasets", "files", sys.argv[1]],
                          capture_output=True, text=True).stdout
    files = {}
    for line in out.splitlines()[2:]:  # skip header + separator
        parts = line.split()
        if len(parts) >= 2:
            try:
                files[parts[0]] = int(parts[1])
            except ValueError:
                continue
    return files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dataset_ref", help="owner/dataset-slug")
    ap.add_argument("local_file", type=Path)
    ap.add_argument("kaggle_filename")
    ap.add_argument("--message", default=None)
    ap.add_argument("--title", default=None, help="dataset title, only used if creating new")
    args = ap.parse_args()

    if not args.local_file.exists():
        print(f"ERROR: {args.local_file} not found", file=sys.stderr)
        sys.exit(1)
    new_bytes = args.local_file.stat().st_size

    before = dataset_files()
    print(f"Current dataset has {len(before)} file(s): {sorted(before)}")

    with tempfile.TemporaryDirectory() as tmpdir:
        stage = Path(tmpdir)
        if before:
            r = subprocess.run(
                ["kaggle", "datasets", "download", "-d", args.dataset_ref,
                 "-p", str(stage), "--unzip"],
                capture_output=True, text=True,
            )
            if r.returncode != 0:
                print(f"ERROR: could not download existing dataset to merge "
                      f"into - refusing to proceed (would replace instead of "
                      f"add): {r.stderr}", file=sys.stderr)
                sys.exit(1)
            # dataset-metadata.json comes down with the download; keep it.

        shutil.copy2(args.local_file, stage / args.kaggle_filename)

        meta_path = stage / "dataset-metadata.json"
        if not meta_path.exists():
            title = args.title or args.dataset_ref.split("/")[-1]
            meta_path.write_text(
                f'{{"id": "{args.dataset_ref}", "title": "{title}", '
                f'"licenses": [{{"name": "CC0-1.0"}}]}}'
            )

        msg = args.message or f"add/update {args.kaggle_filename}"
        if before:
            r = subprocess.run(
                ["kaggle", "datasets", "version", "-p", str(stage), "-m", msg],
                capture_output=True, text=True,
            )
        else:
            r = subprocess.run(["kaggle", "datasets", "create", "-p", str(stage)],
                                capture_output=True, text=True)
        print(r.stdout, r.stderr)

    # Positive verification: check the ACTUAL post-upload file listing, not
    # the CLI's exit code (title-collision errors have printed and still
    # exited 0 before). Confirms both the new file AND every pre-existing
    # file survived the version bump. Poll on SIZE MATCH, not just filename
    # presence - Kaggle's file listing can show the filename with the
    # PREVIOUS version's byte size for a while after `datasets version`
    # returns, while the backend is still committing the new version. An
    # early break on presence-only (the original bug here, found 2026-08-08
    # against a real upload that succeeded but was reported as failed)
    # produces a false failure. Keep polling the full budget until the size
    # matches or attempts are exhausted.
    confirmed = None
    last_seen_size = None
    attempts, poll_interval_s = 24, 10  # up to 4 min - Kaggle version-commit lag observed >60s
    for _ in range(attempts):
        time.sleep(poll_interval_s)
        after = dataset_files()
        last_seen_size = after.get(args.kaggle_filename)
        if last_seen_size == new_bytes:
            confirmed = after
            break
    if confirmed is None:
        if last_seen_size is None:
            print(f"ERROR: new file not confirmed in dataset listing after "
                  f"{attempts * poll_interval_s}s of polling", file=sys.stderr)
        else:
            print(f"ERROR: size mismatch for {args.kaggle_filename} after "
                  f"{attempts * poll_interval_s}s of polling - expected "
                  f"{new_bytes}, found {last_seen_size} (Kaggle version-commit "
                  f"may still be in progress - re-check with "
                  f"'kaggle datasets files {args.dataset_ref}' before assuming "
                  f"data loss)", file=sys.stderr)
        sys.exit(1)

    dropped = [f for f in before if f not in confirmed]
    if dropped:
        print(f"ERROR: {len(dropped)} previously-present file(s) missing after "
              f"upload - {dropped}. This should be impossible with this script's "
              f"download-merge-reupload pattern; investigate immediately.",
              file=sys.stderr)
        sys.exit(1)

    print(f"OK: {args.kaggle_filename} ({new_bytes/1e6:.1f}MB) confirmed in "
          f"{args.dataset_ref}, all {len(before)} pre-existing file(s) intact.")


if __name__ == "__main__":
    main()

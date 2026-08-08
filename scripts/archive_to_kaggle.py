#!/usr/bin/env python3
"""
Repo-hygiene workflow (2026-08-07 user decision: large source files move to
Kaggle, git keeps only a pointer). Uploads a large, standalone source file
(not one a Remotion app needs physically present to render - see
sync_remotion_public.py for that separate case) to a dedicated Kaggle
dataset, records a pointer in the owning project's
state/kaggle_archive.jsonl, and untracks the file from git (git rm, file
stays on local disk - CLAUDE.md "never delete", the Kaggle copy + this
pointer record together ARE the archive).

Only for genuinely standalone files: raw upload zips, source PDFs that
nothing at render time reads directly. Do not point this at anything under
a remotion_*/public/ dir or anything referenced by scenesData.ts/timeline -
those need to stay locally readable.

Two Kaggle-API gotchas this script works around (found the hard way, see
git history around 2026-08-07):
1. `kaggle datasets version -p <dir>` REPLACES the dataset's entire content
   set with whatever is in <dir> - it does not merge/append across calls.
   So every run downloads the dataset's current full file list first, adds
   the new file to that local copy, and re-uploads everything together.
2. Kaggle silently auto-extracts any `.zip` it finds in the upload dir
   instead of storing it as one file. Staged files get a `.bin` suffix
   appended to their real name to opt out of that.

Usage:
    python3 scripts/archive_to_kaggle.py <file_path> <project_id>

Dataset: mehmetkync16/studio-large-source-assets (private).
"""
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
KAGGLE_DATASET_SLUG = "studio-large-source-assets"
KAGGLE_USER = "mehmetkync16"
KAGGLE_REF = f"{KAGGLE_USER}/{KAGGLE_DATASET_SLUG}"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def dataset_exists() -> bool:
    # `kaggle datasets list -m` has been observed stale/unreliable right after
    # a create (false negative -> spurious duplicate-title create attempts).
    # `datasets metadata` is a direct lookup, no listing/indexing lag.
    with tempfile.TemporaryDirectory() as tmpdir:
        r = subprocess.run(
            ["kaggle", "datasets", "metadata", KAGGLE_REF, "-p", tmpdir],
            capture_output=True, text=True,
        )
        return r.returncode == 0


def uploaded_file_size(kaggle_filename: str) -> int | None:
    """Positive verification: exit codes/stderr text from the Kaggle CLI have
    proven unreliable for detecting failure (a title-collision 'error' on
    `datasets create` still returned exit 0 - see module docstring). Instead
    of trusting the CLI's own success signal, check the dataset's actual file
    listing for the exact filename+size we expect."""
    out = subprocess.run(["kaggle", "datasets", "files", KAGGLE_REF], capture_output=True, text=True).stdout
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0] == kaggle_filename:
            try:
                return int(parts[1])
            except ValueError:
                return None
    return None


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    file_path = Path(sys.argv[1]).resolve()
    project_id = sys.argv[2]
    if not file_path.exists():
        print(f"ERROR: {file_path} not found", file=sys.stderr)
        sys.exit(1)

    rel_path = file_path.relative_to(REPO_ROOT)
    file_sha256 = sha256_file(file_path)
    file_bytes = file_path.stat().st_size
    kaggle_filename = f"{project_id}__{file_path.name}.bin"  # .bin opts out of zip auto-extraction

    with tempfile.TemporaryDirectory() as tmpdir:
        stage = Path(tmpdir)
        exists = dataset_exists()

        if exists:
            r = subprocess.run(
                ["kaggle", "datasets", "download", "-d", KAGGLE_REF, "-p", str(stage), "--unzip"],
                capture_output=True, text=True,
            )
            if r.returncode != 0:
                print(f"ERROR: could not download existing dataset to merge into: {r.stderr}", file=sys.stderr)
                sys.exit(1)

        shutil.copy2(file_path, stage / kaggle_filename)
        meta = {"title": "Studio Large Source Assets", "id": KAGGLE_REF, "licenses": [{"name": "CC0-1.0"}]}
        (stage / "dataset-metadata.json").write_text(json.dumps(meta, indent=2))

        if exists:
            r = subprocess.run(
                ["kaggle", "datasets", "version", "-p", str(stage), "-m", f"archive {kaggle_filename}",
                 "-r", "zip", "--delete-old-versions"],
                capture_output=True, text=True,
            )
        else:
            r = subprocess.run(["kaggle", "datasets", "create", "-p", str(stage)], capture_output=True, text=True)

        print(r.stdout, r.stderr)

        # Positive verification (see uploaded_file_size docstring) - Kaggle
        # processes the upload asynchronously, so poll briefly before
        # declaring failure.
        import time
        confirmed_size = None
        for _ in range(6):
            time.sleep(5)
            confirmed_size = uploaded_file_size(kaggle_filename)
            if confirmed_size is not None:
                break
        if confirmed_size != file_bytes:
            print(
                f"ERROR: kaggle upload not verified - expected {kaggle_filename} "
                f"at {file_bytes} bytes, found {confirmed_size}. NOT writing a "
                f"pointer or untracking the local file.",
                file=sys.stderr,
            )
            sys.exit(1)

    state_dir = REPO_ROOT / "projects" / project_id / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    archive_log = state_dir / "kaggle_archive.jsonl"
    entry = {
        "original_path": str(rel_path),
        "sha256": file_sha256,
        "bytes": file_bytes,
        "kaggle_dataset": KAGGLE_REF,
        "kaggle_filename": kaggle_filename,
        "kaggle_url": f"https://www.kaggle.com/datasets/{KAGGLE_REF}",
    }
    with open(archive_log, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"Uploaded {rel_path} ({file_bytes/1e6:.1f}MB) -> Kaggle, pointer written to {archive_log}")
    print(f"Run: git rm --cached {rel_path}  (keeps the file on local disk, only untracks it)")


if __name__ == "__main__":
    main()

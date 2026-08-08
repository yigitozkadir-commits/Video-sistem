#!/usr/bin/env python3
"""
Copies a project's canonical assets (projects/<id>/assets/{still,video,audio})
into a Remotion app's public/ dir, where Remotion needs them physically
present to render (its dev server refuses to follow symlinks outside
public/, confirmed empirically - see repo history around 2026-08-07).

Why this exists: those public/ copies were being git-tracked as full
duplicate bytes alongside the canonical projects/ copies - ~290MB of
identical content for the atlas and fairytale (studio) projects alone.
public/{still,video,audio} for those two apps is now gitignored; this
script is how you regenerate it locally (once after a fresh clone, or
whenever new assets are added to a project) instead of double-tracking it.

Only safe for projects where the Remotion public/ filename matches the
project asset filename exactly (verified for gok-umay-atlasi and
daglar-uyuyan-devleri: every public/ file is byte-identical to a
same-named projects/assets/ file). PRJ-baskurtlar-arastirma's remotion
public/still/ filenames do NOT match its project asset filenames 1:1
(a selection/rename step happens during ingestion) - do not point this
script at remotion_baskurtlar without first building that mapping.

Usage:
    python3 scripts/sync_remotion_public.py <project_id> <remotion_dir>

Example:
    python3 scripts/sync_remotion_public.py PRJ-gok-umay-atlasi remotion_atlas
    python3 scripts/sync_remotion_public.py PRJ-daglar-uyuyan-devleri remotion_studio
"""
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
SUBDIRS = ("still", "video", "audio")


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    project_id, remotion_dir = sys.argv[1], sys.argv[2]

    assets_root = REPO_ROOT / "projects" / project_id / "assets"
    public_root = REPO_ROOT / remotion_dir / "public"
    if not assets_root.exists():
        print(f"ERROR: {assets_root} not found", file=sys.stderr)
        sys.exit(1)
    # public_root itself is not guaranteed to exist on a fresh checkout: if
    # every file under it is gitignored (true for atlas/studio's still/video/
    # audio), git never materializes the directory at all - found by actually
    # running this on a clean GitHub Actions checkout, 2026-08-07. Create it
    # rather than erroring; it previously only "worked" locally because a
    # long-lived dev container had already created it once and never deleted
    # it, which a real fresh clone (CI or a human) would never have.
    public_root.mkdir(parents=True, exist_ok=True)

    total = 0
    for sub in SUBDIRS:
        src_dir = assets_root / sub
        if not src_dir.exists():
            continue
        dst_dir = public_root / sub
        dst_dir.mkdir(parents=True, exist_ok=True)
        n = 0
        for src_file in src_dir.iterdir():
            if not src_file.is_file():
                continue
            shutil.copy2(src_file, dst_dir / src_file.name)
            n += 1
        print(f"  {sub}: synced {n} files -> {dst_dir}")
        total += n

    print(f"Synced {total} files total.")


if __name__ == "__main__":
    main()

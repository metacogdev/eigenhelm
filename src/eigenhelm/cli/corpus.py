"""eigenhelm-corpus: CLI entry point for corpus operations."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> None:
    """Entry point for eigenhelm-corpus CLI.

    Exit codes:
        0 — all targets synced or skipped successfully
        1 — manifest parsing or validation error; nothing downloaded
        2 — one or more targets failed during download/extraction
    """
    parser = argparse.ArgumentParser(
        prog="eigenhelm-corpus",
        description="Manage eigenhelm training corpora.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    sync_parser = subparsers.add_parser(
        "sync",
        help="Materialize a corpus manifest into a local directory.",
    )
    sync_parser.add_argument(
        "manifest_path",
        type=Path,
        metavar="manifest-path",
        help="Path to the .toml manifest file.",
    )
    sync_parser.add_argument(
        "output_dir",
        type=Path,
        metavar="output-dir",
        help="Directory to materialize the corpus into.",
    )
    sync_parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download all targets even if already present.",
    )

    args = parser.parse_args(argv)

    if args.command == "sync":
        sys.exit(_cmd_sync(args))


def _cmd_sync(args: argparse.Namespace) -> int:
    from eigenhelm.corpus.manifest import load_manifest
    from eigenhelm.corpus.sync import sync_manifest

    try:
        manifest = load_manifest(args.manifest_path)
    except FileNotFoundError as exc:
        print(f"eigenhelm-corpus sync: error: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"eigenhelm-corpus sync: error: {exc}", file=sys.stderr)
        return 1

    n = len(manifest.targets)
    print(f"eigenhelm-corpus sync: Syncing {n} targets to {args.output_dir}")

    result = sync_manifest(manifest, args.output_dir, force=args.force)

    # Print per-target results in manifest order
    failed_dict = dict(result.failed)
    skipped_set = set(result.skipped)
    synced_set = set(result.synced)

    for i, target in enumerate(manifest.targets, 1):
        name = target.name
        if name in skipped_set:
            print(f"  [{i}/{n}] {name:<12s} already present  (skipped)")
        elif name in synced_set:
            k = result.files_by_target.get(name, 0)
            print(f"  [{i}/{n}] {name:<12s} fetching...  done  ({k} files)")
        elif name in failed_dict:
            print(
                f"eigenhelm-corpus sync: error: {name} — {failed_dict[name]}",
                file=sys.stderr,
            )

    # Summary line
    n_synced = len(result.synced)
    n_skipped = len(result.skipped)
    n_failed = len(result.failed)
    total = result.total_files
    summary = (
        f"eigenhelm-corpus sync: Complete"
        f"  {n_synced} synced  {n_skipped} skipped  {n_failed} failed"
    )
    if n_synced > 0:
        summary += f"  ({total} files total)"
    print(summary)

    return 2 if result.failed else 0

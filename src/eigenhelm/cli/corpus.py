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
    group = sync_parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "manifest_path",
        type=Path,
        nargs="?",
        metavar="manifest-path",
        help="Path to the .toml manifest file.",
    )
    group.add_argument(
        "--all",
        dest="scan_dir",
        type=Path,
        metavar="directory",
        help="Scan directory for all .toml manifests and sync each.",
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
        if args.scan_dir is not None:
            sys.exit(_cmd_sync_all(args))
        else:
            sys.exit(_cmd_sync(args))


def _cmd_sync(args: argparse.Namespace) -> int:
    from eigenhelm.corpus.manifest import (
        CompositionManifest,
        load_any_manifest,
    )

    try:
        loaded = load_any_manifest(args.manifest_path)
    except FileNotFoundError as exc:
        print(f"eigenhelm-corpus sync: error: {exc}", file=sys.stderr)
        return 1
    except (ValueError, Exception) as exc:
        print(f"eigenhelm-corpus sync: error: {exc}", file=sys.stderr)
        return 1

    if isinstance(loaded, CompositionManifest):
        return _sync_composition(loaded, args)

    return _sync_single(loaded, args)


def _sync_single(manifest, args: argparse.Namespace) -> int:
    from eigenhelm.corpus.sync import sync_manifest

    n = len(manifest.targets)
    print(f"eigenhelm-corpus sync: Syncing {n} targets to {args.output_dir}")

    result = sync_manifest(manifest, args.output_dir, force=args.force)

    _print_sync_result(result, manifest.targets)
    return 2 if result.failed else 0


def _sync_composition(composition, args: argparse.Namespace) -> int:
    from eigenhelm.corpus.sync import sync_composition

    base_dir = args.manifest_path.resolve().parent
    print(
        f"eigenhelm-corpus sync: Composition '{composition.name}' "
        f"— {len(composition.sources)} sources"
    )

    try:
        bulk = sync_composition(
            composition, base_dir, args.output_dir, force=args.force
        )
    except FileNotFoundError as exc:
        print(f"eigenhelm-corpus sync: error: {exc}", file=sys.stderr)
        return 1

    _print_bulk_result(bulk)
    return 2 if bulk.any_failed else 0


def _cmd_sync_all(args: argparse.Namespace) -> int:
    from eigenhelm.corpus.sync import sync_all_manifests

    scan_dir = args.scan_dir
    print(f"eigenhelm-corpus sync --all: Scanning {scan_dir}")

    bulk = sync_all_manifests(scan_dir, args.output_dir, force=args.force)

    _print_bulk_result(bulk)
    return 2 if bulk.any_failed else 0


def _print_sync_result(result, targets) -> None:
    failed_dict = dict(result.failed)
    skipped_set = set(result.skipped)
    synced_set = set(result.synced)
    n = len(targets)

    for i, target in enumerate(targets, 1):
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


def _print_bulk_result(bulk) -> None:
    for name, sr in bulk.per_manifest.items():
        n_synced = len(sr.synced)
        n_skipped = len(sr.skipped)
        n_failed = len(sr.failed)
        total = sr.total_files
        status = f"  {name}: {n_synced} synced  {n_skipped} skipped  {n_failed} failed"
        if n_synced > 0:
            status += f"  ({total} files)"
        print(status)

    for manifest_name, error in bulk.failed_manifests:
        print(
            f"eigenhelm-corpus sync: error: {manifest_name} — {error}",
            file=sys.stderr,
        )

    total_manifests = len(bulk.per_manifest) + len(bulk.failed_manifests)
    print(
        f"eigenhelm-corpus sync: {total_manifests} manifests processed, "
        f"{len(bulk.failed_manifests)} failed"
    )

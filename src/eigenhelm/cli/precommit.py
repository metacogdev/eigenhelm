"""eigenhelm-check — pre-commit hook for eigenhelm evaluation.

Evaluates staged files against the aesthetic manifold and blocks commits
on reject decisions (or warn with --strict). Uses a content-hash cache
to avoid re-evaluating unchanged files.
"""

from __future__ import annotations

import argparse
from eigenhelm.cli._common import add_strict_lenient_args
import hashlib
import subprocess
import sys
from pathlib import Path

from eigenhelm.cli._shared import _apply_thresholds

# Re-exported for backwards compatibility (tests and external callers import these from here)
from eigenhelm.cli.precommit_cache import (
    _CACHE_FILE,
    CacheEntry,
    EvaluationCache,
)
from eigenhelm.config import find_config, load_config
from eigenhelm.helm import DynamicHelm
from eigenhelm.helm.models import EvaluationRequest
from eigenhelm.parsers.language_map import LANGUAGE_MAP

_RECOGNIZED_EXTENSIONS: frozenset[str] = frozenset(
    ext for _, (_, ext) in LANGUAGE_MAP.items()
)
_EXT_TO_LANG: dict[str, str] = {ext: lang for lang, (_, ext) in LANGUAGE_MAP.items()}


def _hash_file(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _hash_config(config_path: Path | None) -> str:
    if config_path is None or not config_path.exists():
        return ""
    return hashlib.sha256(config_path.read_bytes()).hexdigest()


def _get_staged_files() -> list[Path]:
    """Return list of staged files with recognized extensions."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return []

    if result.returncode != 0:
        return []

    paths = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        p = Path(line)
        if p.suffix in _RECOGNIZED_EXTENSIONS and p.is_file():
            paths.append(p)
    return paths


def _load_project_config() -> tuple[object | None, Path | None, bool, str]:
    """Find and load project config, determine strict mode base, and config hash.

    Returns:
        (config, config_path, config_strict, config_hash) where config_strict
        is True only if the config file sets strict mode.
    """
    config = None
    config_path: Path | None = None
    try:
        config_path = find_config(Path.cwd())
        if config_path is not None:
            config = load_config(config_path)
    except Exception:
        pass

    config_strict = config is not None and config.strict
    config_hash = _hash_config(config_path)
    return config, config_path, config_strict, config_hash


def _evaluate_staged_file(
    file_path: Path,
    helm: DynamicHelm,
    cache: EvaluationCache,
    config: object | None,
    lang_overrides: dict[str, str],
    collect_scorecard: bool,
) -> tuple[str | None, float | None, bool, tuple[str, object] | None]:
    """Evaluate a single staged file with cache check.

    Returns:
        (decision, score, was_evaluated, scorecard_entry) where:
        - decision is None if the file was skipped
        - was_evaluated is True only when the file was freshly evaluated (not cached)
        - scorecard_entry is (path_str, critique) if collect_scorecard else None
    """
    try:
        content = file_path.read_bytes()
    except OSError:
        return None, None, False, None

    content_hash = _hash_file(content)
    path_str = str(file_path)

    # Check cache
    cached = cache.get(path_str, content_hash)
    if cached is not None:
        print(f"  [cache] {file_path}: {cached.decision} (score={cached.score:.2f})")
        return cached.decision, cached.score, False, None

    # Resolve language
    lang = lang_overrides.get(file_path.suffix) or _EXT_TO_LANG.get(file_path.suffix)
    if lang is None:
        return None, None, False, None

    try:
        source = content.decode("utf-8")
    except UnicodeDecodeError:
        print(
            f"  WARNING: Skipping binary file {file_path}",
            file=sys.stderr,
        )
        return None, None, False, None

    resp = helm.evaluate(
        EvaluationRequest(source=source, language=lang, file_path=path_str)
    )

    # Apply per-file thresholds from config
    if config is not None:
        thresholds = config.thresholds_for(path_str)
        resp = _apply_thresholds(resp, thresholds)

    decision = resp.decision
    score = resp.score
    print(f"  {file_path}: {decision} (score={score:.2f})")

    scorecard_entry = (path_str, resp.critique) if collect_scorecard else None

    cache.set(
        path_str,
        CacheEntry(
            content_hash=content_hash,
            decision=decision,
            score=score,
        ),
    )
    return decision, score, True, scorecard_entry


def main(argv: list[str] | None = None) -> int:
    """Entry point for eigenhelm-check pre-commit hook.

    Returns:
        0  All staged files accepted or warned (or cache hit)
        1  At least one staged file rejected
        2  Runtime error
    """
    parser = argparse.ArgumentParser(
        prog="eigenhelm-check",
        description="eigenhelm pre-commit hook — evaluate staged files",
    )
    add_strict_lenient_args(parser)
    parser.add_argument(
        "--scorecard",
        action="store_true",
        default=False,
        help="Print per-repository scorecard after evaluation.",
    )
    args = parser.parse_args(argv or [])

    try:
        config, _config_path, config_strict, config_hash = _load_project_config()
        strict = args.strict or (config_strict and not args.lenient)

        # Load cache
        cache = EvaluationCache(_CACHE_FILE, config_hash)

        # Discover staged files
        staged = _get_staged_files()
        if not staged:
            print("eigenhelm-check: no staged source files to evaluate.")
            return 0

        lang_overrides = config.language_overrides if config else {}

        from eigenhelm.cli._common import resolve_and_load_model

        eigenspace, _ = resolve_and_load_model(None, config)

        helm = DynamicHelm(eigenspace=eigenspace)

        any_reject = False
        evaluated = 0
        cached_hits = 0
        scorecard_critiques: list[tuple[str, object]] = []

        for file_path in staged:
            decision, _score, was_evaluated, scorecard_entry = _evaluate_staged_file(
                file_path, helm, cache, config, lang_overrides, args.scorecard
            )

            if decision is None:
                continue

            if was_evaluated:
                evaluated += 1
            else:
                cached_hits += 1

            if scorecard_entry is not None:
                scorecard_critiques.append(scorecard_entry)

            effective_decision = decision
            if strict and effective_decision == "warn":
                effective_decision = "reject"

            if effective_decision == "reject":
                any_reject = True

        cache.save()

        if args.scorecard and scorecard_critiques:
            from eigenhelm.scoring.scorecard import (
                build_scorecard,
            )
            from eigenhelm.scoring.scorecard import (
                render_human as render_scorecard_human,
            )

            scorecard = build_scorecard(scorecard_critiques)
            print(render_scorecard_human(scorecard))

        if any_reject:
            print(
                "\neigenhelm-check: BLOCKED — one or more files rejected.",
                file=sys.stderr,
            )
            return 1

        hits_msg = f" ({cached_hits} cached)" if cached_hits else ""
        print(f"\neigenhelm-check: OK — {evaluated} evaluated{hits_msg}.")
        return 0

    except Exception as exc:
        print(f"eigenhelm-check ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

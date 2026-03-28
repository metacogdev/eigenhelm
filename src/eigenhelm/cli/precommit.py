"""eigenhelm-check — pre-commit hook for eigenhelm evaluation.

Evaluates staged files against the aesthetic manifold and blocks commits
on reject decisions (or warn with --strict). Uses a content-hash cache
to avoid re-evaluating unchanged files.

Cache file: .eigenhelm/cache.json
Format:
  {
    "version": 1,
    "config_hash": "<SHA-256 of .eigenhelm.toml contents>",
    "entries": {
      "path/to/file.py": {
        "content_hash": "<SHA-256>",
        "decision": "accept",
        "score": 0.2
      }
    }
  }
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

from eigenhelm.config import find_config, load_config
from eigenhelm.helm import DynamicHelm
from eigenhelm.helm.models import EvaluationRequest, EvaluationResponse
from eigenhelm.parsers.language_map import LANGUAGE_MAP

_RECOGNIZED_EXTENSIONS: frozenset[str] = frozenset(
    ext for _, (_, ext) in LANGUAGE_MAP.items()
)
_EXT_TO_LANG: dict[str, str] = {ext: lang for lang, (_, ext) in LANGUAGE_MAP.items()}
_CACHE_VERSION = 1
_CACHE_FILE = Path(".eigenhelm") / "cache.json"


@dataclass
class CacheEntry:
    content_hash: str
    decision: str
    score: float


class EvaluationCache:
    """Content-hash cache for pre-commit evaluations.

    Invalidated when .eigenhelm.toml changes (via config_hash).
    """

    def __init__(self, cache_path: Path, config_hash: str) -> None:
        self._path = cache_path
        self._config_hash = config_hash
        self._entries: dict[str, CacheEntry] = {}
        self._load()

    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            if data.get("version") != _CACHE_VERSION:
                return  # Incompatible version
            if data.get("config_hash") != self._config_hash:
                return  # Config changed — invalidate
            for path_str, entry_data in data.get("entries", {}).items():
                self._entries[path_str] = CacheEntry(**entry_data)
        except (json.JSONDecodeError, KeyError, TypeError):
            pass  # Corrupt cache — start fresh

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": _CACHE_VERSION,
            "config_hash": self._config_hash,
            "entries": {k: asdict(v) for k, v in self._entries.items()},
        }
        self._path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def get(self, path: str, content_hash: str) -> CacheEntry | None:
        """Return cached entry if the content hash matches, else None."""
        entry = self._entries.get(path)
        if entry is not None and entry.content_hash == content_hash:
            return entry
        return None

    def set(self, path: str, entry: CacheEntry) -> None:
        self._entries[path] = entry


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


def _apply_thresholds(response: EvaluationResponse, thresholds) -> EvaluationResponse:
    """Re-derive decision from score using config thresholds."""
    from dataclasses import replace

    score = response.score
    if score >= thresholds.reject:
        new_decision = "reject"
    elif score <= thresholds.accept:
        new_decision = "accept"
    else:
        new_decision = "warn"

    if new_decision == response.decision:
        return response
    return replace(response, decision=new_decision)


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
    strict_group = parser.add_mutually_exclusive_group()
    strict_group.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="Treat warn as reject (block commit on warn).",
    )
    strict_group.add_argument(
        "--lenient",
        action="store_true",
        default=False,
        help="Treat warn as accept (override config strict).",
    )
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

        eigenspace = None
        if config is not None and config.model:
            try:
                from eigenhelm.eigenspace import load_model

                eigenspace = load_model(config.model)
            except Exception:
                pass

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

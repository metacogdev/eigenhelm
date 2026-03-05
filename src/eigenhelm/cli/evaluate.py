"""eigenhelm-evaluate CLI — evaluate files in-process.

Usage:
    eigenhelm-evaluate path/to/file.py
    eigenhelm-evaluate src/ --model model.npz
    echo "def f(): pass" | eigenhelm-evaluate --language python
    eigenhelm-evaluate src/ --json

Exit codes:
    0  All files accepted or warned
    1  One or more files rejected
    2  Runtime error
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from eigenhelm.helm import DynamicHelm
from eigenhelm.helm.models import EvaluationRequest, EvaluationResponse
from eigenhelm.parsers.language_map import LANGUAGE_MAP

# Build extension → language mapping from LANGUAGE_MAP
EXTENSION_TO_LANGUAGE: dict[str, str] = {ext: lang for lang, (_, ext) in LANGUAGE_MAP.items()}


DEFAULT_EXCLUDES = {
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    "node_modules",
    ".pytest_cache",
    "dist",
    "build",
}


def _load_excludes(dir_path: Path) -> set[str]:
    """Load custom excludes from .eigenhelmignore if it exists."""
    excludes = set(DEFAULT_EXCLUDES)
    ignore_file = dir_path / ".eigenhelmignore"
    if ignore_file.is_file():
        try:
            lines = ignore_file.read_text().splitlines()
            custom = [line.strip() for line in lines if line.strip() and not line.startswith("#")]
            excludes.update(custom)
        except OSError:
            pass
    return excludes


def _walk_directory(dir_path: Path, excludes: set[str]) -> list[tuple[Path, str]]:
    """Recursively walk directory and find eligible source files."""
    results: list[tuple[Path, str]] = []
    for root, dirs, files in os.walk(dir_path, followlinks=False):
        # Prune excluded directories
        retained = [d for d in dirs if d not in excludes and not d.endswith(".egg-info")]
        dirs.clear()
        dirs.extend(retained)

        for filename in files:
            if filename in excludes:
                continue
            child = Path(root) / filename
            try:
                if child.is_symlink() or not child.is_file():
                    continue
                lang = EXTENSION_TO_LANGUAGE.get(child.suffix)
                if lang is not None:
                    results.append((child, lang))
            except OSError:
                continue
    return results


def discover_files(paths: list[Path]) -> list[tuple[Path, str]]:
    """Discover eligible source files from given paths.

    Returns (path, language) pairs sorted by path.
    """
    results: list[tuple[Path, str]] = []
    for p in paths:
        if p.is_file():
            lang = EXTENSION_TO_LANGUAGE.get(p.suffix)
            if lang:
                results.append((p, lang))
            else:
                print(f"WARNING: Skipping {p} (unknown extension)", file=sys.stderr)
        elif p.is_dir():
            excludes = _load_excludes(p)
            results.extend(_walk_directory(p, excludes))

    return sorted(results, key=lambda x: x[0])


def format_result_human(path: Path | str, response: EvaluationResponse) -> str:
    """Format a single result for human-readable output."""
    lines = [
        f"{path}",
        f"  decision: {response.decision}",
        f"  score:    {response.score:.2f}",
        f"  confidence: {response.structural_confidence}",
    ]
    if response.critique.violations:
        lines.append("  violations:")
        for v in response.critique.violations:
            pct = v.contribution * 100
            lines.append(f"    {v.dimension} (contribution: {pct:.0f}%)")
    if response.warning:
        lines.append(f"  warning: {response.warning}")
    return "\n".join(lines)


def format_summary_human(
    results: list[tuple[Path | str, EvaluationResponse]],
) -> str:
    """Format aggregate summary for human-readable output."""
    total = len(results)
    accepted = sum(1 for _, r in results if r.decision == "accept")
    warned = sum(1 for _, r in results if r.decision == "warn")
    rejected = sum(1 for _, r in results if r.decision == "reject")
    mean_score = sum(r.score for _, r in results) / total if total else 0.0
    sep = "─" * 40
    return (
        f"{sep}\n"
        f"Summary: {total} files | {accepted} accepted | {warned} warned | "
        f"{rejected} rejected | mean score: {mean_score:.2f}"
    )


def format_results_json(
    results: list[tuple[Path | str, EvaluationResponse]],
) -> str:
    """Format results as JSON matching BatchResponse schema."""
    result_dicts = []
    for path, resp in results:
        violations = [
            {
                "dimension": v.dimension,
                "raw_value": v.raw_value,
                "normalized_value": v.normalized_value,
                "contribution": v.contribution,
            }
            for v in resp.critique.violations
        ]
        result_dicts.append(
            {
                "decision": resp.decision,
                "score": resp.score,
                "structural_confidence": resp.structural_confidence,
                "violations": violations,
                "warning": resp.warning,
                "file_path": str(path),
            }
        )

    total = len(result_dicts)
    accepted = sum(1 for r in result_dicts if r["decision"] == "accept")
    warned = sum(1 for r in result_dicts if r["decision"] == "warn")
    rejected = sum(1 for r in result_dicts if r["decision"] == "reject")
    mean_score = sum(r["score"] for r in result_dicts) / total if total else 0.0

    if rejected > 0:
        overall = "reject"
    elif warned > 0:
        overall = "warn"
    else:
        overall = "accept"

    output = {
        "results": result_dicts,
        "summary": {
            "overall_decision": overall,
            "total_files": total,
            "accepted": accepted,
            "warned": warned,
            "rejected": rejected,
            "mean_score": mean_score,
        },
    }
    return json.dumps(output, indent=2)


def _evaluate_stdin(
    helm: DynamicHelm,
    language: str,
) -> list[tuple[Path | str, EvaluationResponse]]:
    """Read from stdin and evaluate."""
    source = sys.stdin.read()
    resp = helm.evaluate(EvaluationRequest(source=source, language=language))
    return [("<stdin>", resp)]


def _evaluate_paths(
    helm: DynamicHelm,
    paths: list[Path],
) -> list[tuple[Path | str, EvaluationResponse]]:
    """Discover and evaluate files from given paths."""
    files = discover_files(paths)
    results: list[tuple[Path | str, EvaluationResponse]] = []
    for path, lang in files:
        try:
            source = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            print(f"WARNING: Skipping binary file {path}", file=sys.stderr)
            continue
        resp = helm.evaluate(EvaluationRequest(source=source, language=lang, file_path=str(path)))
        results.append((path, resp))
    return results


def main(argv: list[str] | None = None) -> int:
    """Entry point for eigenhelm-evaluate.

    Returns exit code: 0 (no rejections), 1 (any rejection), 2 (runtime error).
    """
    parser = argparse.ArgumentParser(
        prog="eigenhelm-evaluate",
        description="Evaluate code files against the aesthetic manifold",
    )
    parser.add_argument("paths", nargs="*", type=Path, help="File or directory paths")
    parser.add_argument(
        "--language",
        default=None,
        help="Language (required for stdin mode when no paths given)",
    )
    parser.add_argument("--model", default=None, help="Path to .npz eigenspace model")
    parser.add_argument("--json", dest="json_output", action="store_true", help="JSON output")
    args = parser.parse_args(argv)

    try:
        eigenspace = None
        if args.model:
            from eigenhelm.eigenspace import load_model

            eigenspace = load_model(args.model)

        helm = DynamicHelm(eigenspace=eigenspace)

        if not args.paths:
            if not args.language:
                print(
                    "ERROR: --language is required when reading from stdin",
                    file=sys.stderr,
                )
                return 2
            results = _evaluate_stdin(helm, args.language)
        else:
            results = _evaluate_paths(helm, args.paths)

        if not results:
            return 0

        if args.json_output:
            print(format_results_json(results))
        else:
            for path, resp in results:
                print(format_result_human(path, resp))
            if len(results) > 1:
                print(format_summary_human(results))

        has_rejection = any(r.decision == "reject" for _, r in results)
        return 1 if has_rejection else 0

    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

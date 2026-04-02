"""eigenhelm-evaluate CLI — evaluate files in-process.

Usage:
    eigenhelm-evaluate path/to/file.py
    eigenhelm-evaluate src/ --model model.npz
    echo "def f(): pass" | eigenhelm-evaluate --language python
    eigenhelm-evaluate src/ --format json
    eigenhelm-evaluate src/ --format sarif
    eigenhelm-evaluate src/ --diff HEAD~1
    eigenhelm-evaluate src/ --strict
    eigenhelm-evaluate src/ --lenient

Exit codes:
    0  All files accepted
    1  At least one file warned (no rejections)
    2  At least one file rejected
    3  Runtime error

Deprecated flags:
    --json  Use --format json instead (emits deprecation warning to stderr)
"""

from __future__ import annotations

import argparse
import importlib.metadata
import os
import sys
from pathlib import Path

from eigenhelm.helm import DynamicHelm
from eigenhelm.helm.models import EvaluationRequest, EvaluationResponse
from eigenhelm.parsers.language_map import LANGUAGE_MAP

# Build extension → language mapping from LANGUAGE_MAP
EXTENSION_TO_LANGUAGE: dict[str, str] = {
    ext: lang for lang, (_, ext) in LANGUAGE_MAP.items()
}


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
            custom = [
                line.strip()
                for line in lines
                if line.strip() and not line.startswith("#")
            ]
            excludes.update(custom)
        except OSError:
            pass
    return excludes


def _walk_directory(
    dir_path: Path,
    excludes: set[str],
    config_excludes: tuple[str, ...] = (),
) -> list[tuple[Path, str]]:
    """Recursively walk directory and find eligible source files."""
    import fnmatch

    results: list[tuple[Path, str]] = []
    for root, dirs, files in os.walk(dir_path, followlinks=False):
        # Prune excluded directories
        retained = []
        for d in dirs:
            if d in excludes or d.endswith(".egg-info"):
                continue
            if config_excludes:
                rel = str(Path(root, d).relative_to(dir_path))
                if any(
                    fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(d, pat)
                    for pat in config_excludes
                ):
                    continue
            retained.append(d)
        dirs.clear()
        dirs.extend(retained)

        for filename in files:
            if filename in excludes:
                continue
            child = Path(root) / filename
            try:
                if child.is_symlink() or not child.is_file():
                    continue
                # Check config exclude patterns against relative path
                if config_excludes:
                    rel = str(child.relative_to(dir_path))
                    if any(
                        fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(filename, pat)
                        for pat in config_excludes
                    ):
                        continue
                lang = EXTENSION_TO_LANGUAGE.get(child.suffix)
                if lang is not None:
                    results.append((child, lang))
            except OSError:
                continue
    return results


def discover_files(
    paths: list[Path],
    language_overrides: dict[str, str] | None = None,
    config_excludes: tuple[str, ...] = (),
) -> list[tuple[Path, str]]:
    """Discover eligible source files from given paths.

    Returns (path, language) pairs sorted by path.

    Args:
        paths: File or directory paths to discover.
        language_overrides: Optional mapping of extension -> language key.
            Overrides LANGUAGE_MAP for matched extensions.
        config_excludes: Glob patterns from .eigenhelm.toml exclude list.
    """
    import fnmatch

    overrides = language_overrides or {}
    results: list[tuple[Path, str]] = []
    for p in paths:
        if p.is_file():
            # Check config excludes against filename and path
            if config_excludes and any(
                fnmatch.fnmatch(p.name, pat) or fnmatch.fnmatch(str(p), pat)
                for pat in config_excludes
            ):
                continue
            lang = overrides.get(p.suffix) or EXTENSION_TO_LANGUAGE.get(p.suffix)
            if lang:
                results.append((p, lang))
            else:
                print(f"WARNING: Skipping {p} (unknown extension)", file=sys.stderr)
        elif p.is_dir():
            excludes = _load_excludes(p)
            for fp, lang in _walk_directory(p, excludes, config_excludes):
                effective_lang = overrides.get(fp.suffix, lang)
                results.append((fp, effective_lang))

    return sorted(results, key=lambda x: x[0])


def format_result_human(
    path: Path | str,
    response: EvaluationResponse,
    classify: bool = False,
) -> str:
    """Format a single result for human-readable output.

    Default mode shows percentile + contribution breakdown (016).
    When classify=True, adds decision label with marginal vocabulary.
    """
    lines = [f"{path}"]

    # Classification label (opt-in only)
    if classify:
        label = "marginal" if response.decision == "warn" else response.decision
        lines.append(f"  decision: {label}")

    # Score line with percentile
    if response.percentile_available and response.percentile is not None:
        pct = round(response.percentile)
        lines.append(
            f"  score:    {response.score:.2f} (p{pct} — better than {pct}% of training corpus)"
        )
    else:
        lines.append(
            f"  score:    {response.score:.2f} (percentile unavailable"
            " — retrain model for percentile data)"
        )

    lines.append(f"  confidence: {response.structural_confidence}")

    # 020: Declaration-heavy tag
    if response.declaration_ratio is not None:
        lines.append("  [declaration-heavy]")

    # 019: Region breakdown (production vs test)
    if response.regions:
        lines.append("  regions:")
        for region in response.regions:
            label = region.label.value
            # Format spans as line ranges
            if len(region.spans) == 1:
                span_str = (
                    f"lines {region.spans[0].start_line}-{region.spans[0].end_line}"
                )
            else:
                span_str = f"{region.total_lines} lines"
            pct_str = (
                f"p{round(region.percentile)}"
                if region.percentile is not None
                else "n/a"
            )
            lines.append(f"    {label} ({span_str}):  {region.score:.2f} ({pct_str})")

    # Per-dimension contribution breakdown (016)
    if response.contributions:
        lines.append("  contributions:")
        for c in response.contributions:
            lines.append(
                f"    {c.dimension:<25s}{c.weighted_contribution:.2f}"
                f"  (weight: {c.weight:.2f}, normalized: {c.normalized_value:.2f})"
            )

    # 017: Attribution directives
    if response.attribution is not None and response.attribution.directives:
        lines.append("  directives:")
        for d in response.attribution.directives:
            loc = d.source_location
            lines.append(
                f"    [{d.severity}] {d.category} → "
                f"{loc.code_unit_name} (lines {loc.start_line}-{loc.end_line})"
            )
            # Show top feature detail for PCA dimensions
            for feat in d.attribution.features[:1]:
                lines.append(
                    f"      #{feat.rank} {feat.feature_name}: "
                    f"contribution={feat.contribution_value:+.2f}, "
                    f"deviation={feat.standardized_deviation:+.1f}σ"
                )

    if response.warning:
        lines.append(f"  warning: {response.warning}")
    return "\n".join(lines)


def format_summary_human(
    results: list[tuple[Path | str, EvaluationResponse]],
    classify: bool = False,
) -> str:
    """Format aggregate summary for human-readable output.

    Default mode (016): shows file count, mean score, mean percentile.
    When classify=True, also shows accept/marginal/reject counts.
    """
    total = len(results)
    mean_score = sum(r.score for _, r in results) / total if total else 0.0
    sep = "─" * 38

    # Compute mean percentile from files that have it available
    pct_values = [
        r.percentile
        for _, r in results
        if r.percentile_available and r.percentile is not None
    ]
    if pct_values:
        mean_pct = sum(pct_values) / len(pct_values)
        pct_part = f" | mean percentile: p{round(mean_pct)}"
    else:
        pct_part = ""

    summary = f"{sep}\nSummary: {total} files | mean score: {mean_score:.2f}{pct_part}"

    if classify:
        accepted = sum(1 for _, r in results if r.decision == "accept")
        warned = sum(1 for _, r in results if r.decision == "warn")
        rejected = sum(1 for _, r in results if r.decision == "reject")
        summary += f"\n{accepted} accepted | {warned} marginal | {rejected} rejected"

    return summary


def format_ranking_human(
    results: list[tuple[Path | str, EvaluationResponse]],
    bottom: int | None = None,
    bottom_pct: float | None = None,
) -> str:
    """Format results as a ranked list with bottom-N highlighting (016).

    Falls back to default percentile mode for single files.
    """
    if len(results) <= 1:
        # Single file: fall back to default mode with note
        if results:
            path, resp = results[0]
            output = format_result_human(path, resp)
            return output + "\n  note: relative ranking requires multiple files"
        return ""

    from eigenhelm.output.percentile import compute_ranking

    ranking_input = [(str(path), resp.score, resp.percentile) for path, resp in results]
    ranking = compute_ranking(ranking_input, bottom=bottom, bottom_pct=bottom_pct)

    lines = [
        f"Ranking: {len(ranking.files)} files evaluated (bottom {ranking.highlight_count} highlighted)"
    ]
    lines.append("")

    for f in ranking.files:
        marker = "* " if f.highlighted else "  "
        pct_str = f"p{round(f.percentile)}" if f.percentile is not None else ""
        tail = "  \u2190 bottom" if f.highlighted else ""
        lines.append(
            f"{marker}#{f.rank:<3d} {f.file_path:<30s} {f.score:.2f}  {pct_str}{tail}"
        )

    lines.append("")
    lines.append(
        f"  spread: {ranking.spread:.2f} | highlighted: {ranking.highlight_count} of {len(ranking.files)}"
    )

    return "\n".join(lines)


def format_results_json(
    results: list[tuple[Path | str, EvaluationResponse]],
) -> str:
    """Format results as JSON matching BatchResponse schema.

    Delegates to eigenhelm.output.json_format.
    """
    from eigenhelm.output.json_format import format_results_json as _fmt

    return _fmt(results)


def compute_exit_code(
    results: list[tuple[Path | str, EvaluationResponse]],
    strict: bool = False,
    lenient: bool = False,
) -> int:
    """Compute exit code from evaluation results.

    Returns:
        0  All files accepted (or lenient mode with warnings)
        1  At least one file warned (no rejections)
        2  At least one file rejected (or strict mode with warnings)
        3  Runtime error — handled by caller, not returned here
    """
    has_reject = any(r.decision == "reject" for _, r in results)
    has_warn = any(r.decision == "warn" for _, r in results)

    if has_reject:
        return 2
    if has_warn:
        if strict:
            return 2
        if lenient:
            return 0
        return 1
    return 0


def _apply_thresholds(
    response: EvaluationResponse,
    thresholds,
) -> EvaluationResponse:
    """Re-derive decision from score using config thresholds.

    Only overrides the decision if at least one config threshold is explicitly set.
    Uses strict boundary semantics matching DynamicHelm: score > reject → reject,
    score < accept → accept, otherwise warn.
    """
    from dataclasses import replace

    accept = thresholds.accept
    reject = thresholds.reject

    # If neither threshold is explicitly configured, no override needed.
    if accept is None and reject is None:
        return response

    score = response.score

    # Apply only the explicitly-set thresholds.
    if reject is not None and score > reject:
        new_decision = "reject"
    elif accept is not None and score < accept:
        new_decision = "accept"
    elif accept is not None and reject is not None:
        # Both set — score is in between, so warn.
        new_decision = "warn"
    else:
        # Only one threshold set and score didn't cross it — leave decision as-is.
        return response

    if new_decision == response.decision:
        return response
    return replace(response, decision=new_decision)


def _evaluate_stdin(
    helm: DynamicHelm,
    language: str,
    top_n: int = 3,
    directive_threshold: float = 0.3,
) -> list[tuple[Path | str, EvaluationResponse]]:
    """Read from stdin and evaluate."""
    source = sys.stdin.read()
    resp = helm.evaluate(
        EvaluationRequest(
            source=source,
            language=language,
            top_n=top_n,
            directive_threshold=directive_threshold,
        )
    )
    resp = _attach_regions(resp, source, language, helm)
    return [("<stdin>", resp)]


def _evaluate_paths(
    helm: DynamicHelm,
    paths: list[Path],
    config=None,
    top_n: int = 3,
    directive_threshold: float = 0.3,
) -> list[tuple[Path | str, EvaluationResponse]]:
    """Discover and evaluate files from given paths."""
    language_overrides = config.language_overrides if config else {}
    config_excludes = config.exclude if config else ()
    files = discover_files(paths, language_overrides, config_excludes)
    results: list[tuple[Path | str, EvaluationResponse]] = []
    from eigenhelm.declarations import analyze_declarations
    from eigenhelm.declarations.barrel import is_barrel_file

    for path, lang in files:
        try:
            source = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            print(f"WARNING: Skipping binary file {path}", file=sys.stderr)
            continue
        if is_barrel_file(source, lang):
            continue
        # Skip pure type-definition files (dataclasses, interfaces, structs)
        # — WL hash signal is syntax noise, not a design smell
        decl = analyze_declarations(source, lang)
        if decl.is_pure_types:
            continue
        resp = helm.evaluate(
            EvaluationRequest(
                source=source,
                language=lang,
                file_path=str(path),
                top_n=top_n,
                directive_threshold=directive_threshold,
            )
        )
        if config is not None:
            thresholds = config.thresholds_for(str(path))
            resp = _apply_thresholds(resp, thresholds)
        # 019: Attach region decomposition if test code detected
        resp = _attach_regions(resp, source, lang, helm)
        results.append((path, resp))
    return results


def _evaluate_diff_paths(
    helm: DynamicHelm,
    revision_range: str,
    config=None,
    top_n: int = 3,
    directive_threshold: float = 0.3,
) -> list[tuple[Path | str, EvaluationResponse]]:
    """Evaluate only files changed in a git revision range."""
    from eigenhelm.diff import discover_changed_files

    changed = discover_changed_files(revision_range)
    if not changed:
        return []
    return _evaluate_paths(
        helm,
        changed,
        config=config,
        top_n=top_n,
        directive_threshold=directive_threshold,
    )


def _attach_regions(
    resp: EvaluationResponse,
    source: str,
    language: str,
    helm: DynamicHelm,
) -> EvaluationResponse:
    """Attach region decomposition to an evaluation response.

    Detects test boundaries, derives spans, scores each region, and returns
    a new response with regions attached. Returns the original response
    unchanged if no test code is detected.
    """
    from dataclasses import replace

    from eigenhelm.regions import derive_spans, detect_test_boundaries

    boundaries = detect_test_boundaries(source, language)
    if not boundaries:
        return resp

    total_lines = len(source.splitlines())
    spans = derive_spans(boundaries, total_lines)
    if not spans:
        return resp

    regions = helm.score_regions(source, language, spans)
    if not regions:
        return resp

    return replace(resp, regions=regions)


def _get_tool_version() -> str:
    try:
        return importlib.metadata.version("eigenhelm")
    except importlib.metadata.PackageNotFoundError:
        return "0.0.0"


def _build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for eigenhelm-evaluate."""
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
    parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="[DEPRECATED] JSON output. Use --format json instead.",
    )
    parser.add_argument(
        "--format",
        dest="output_format",
        choices=["human", "json", "sarif"],
        default=None,
        help="Output format: human (default), json, or sarif.",
    )
    parser.add_argument(
        "--scorecard",
        action="store_true",
        help="Generate per-repository scorecard (M1-M5 mandatory, Q1-Q5 qualitative)",
    )
    strict_group = parser.add_mutually_exclusive_group()
    strict_group.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="Treat warn decisions as reject (exit code 2).",
    )
    strict_group.add_argument(
        "--lenient",
        action="store_true",
        default=False,
        help="Treat warn decisions as accept (exit code 0).",
    )
    parser.add_argument(
        "--diff",
        dest="diff_range",
        default=None,
        metavar="REVISION_RANGE",
        help="Evaluate only files changed in the given git revision range.",
    )
    parser.add_argument(
        "--accept-threshold",
        dest="accept_threshold",
        type=float,
        default=None,
        help="Override accept threshold (overrides model and config).",
    )
    parser.add_argument(
        "--reject-threshold",
        dest="reject_threshold",
        type=float,
        default=None,
        help="Override reject threshold (overrides model and config).",
    )
    # 016: Output mode flags (mutually exclusive)
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--classify",
        action="store_true",
        default=False,
        help="Show accept/marginal/reject labels in human output (opt-in).",
    )
    mode_group.add_argument(
        "--rank",
        action="store_true",
        default=False,
        help="Relative ranking mode: sort files by score, highlight bottom N.",
    )
    # Ranking options (only valid with --rank)
    highlight_group = parser.add_mutually_exclusive_group()
    highlight_group.add_argument(
        "--bottom",
        type=int,
        default=None,
        help="Override highlight count in rank mode.",
    )
    highlight_group.add_argument(
        "--bottom-pct",
        dest="bottom_pct",
        type=float,
        default=None,
        help="Override highlight percentage in rank mode (0-100).",
    )
    # 017: Attribution options
    parser.add_argument(
        "--top-n",
        dest="top_n",
        type=int,
        default=None,
        help="Number of top features per PCA dimension in attribution (default: 3).",
    )
    parser.add_argument(
        "--directive-threshold",
        dest="directive_threshold",
        type=float,
        default=None,
        help="Minimum normalized score to generate directives (default: 0.3).",
    )
    return parser


def _resolve_format(args: argparse.Namespace) -> int | None:
    """Resolve --json / --format flags. Returns error exit code or None on success."""
    if args.json_output and args.output_format is not None:
        print(
            "ERROR: --json and --format are mutually exclusive. Use --format json.",
            file=sys.stderr,
        )
        return 3
    if args.json_output:
        print(
            "DEPRECATION WARNING: --json is deprecated. Use --format json instead.",
            file=sys.stderr,
        )
        args.output_format = "json"
    if args.output_format is None:
        args.output_format = "human"
    # 016: --bottom/--bottom-pct require --rank
    if (args.bottom is not None or args.bottom_pct is not None) and not args.rank:
        print("ERROR: --bottom and --bottom-pct require --rank", file=sys.stderr)
        return 3
    return None


def _load_project_config():
    """Best-effort load of project config. Returns (config, config_path) or (None, None)."""
    try:
        from eigenhelm.config import find_config, load_config

        cfg_path = find_config(Path.cwd())
        if cfg_path is not None:
            return load_config(cfg_path), cfg_path
    except Exception:
        pass
    return None, None


def _render_output(
    results: list[tuple[Path | str, EvaluationResponse]],
    args: argparse.Namespace,
) -> None:
    """Render evaluation results to stdout."""
    if args.scorecard:
        from eigenhelm.scoring.scorecard import (
            build_scorecard,
            render_human as render_scorecard_human,
            render_json as render_scorecard_json,
        )

        file_critiques = [(str(path), resp.critique) for path, resp in results]
        scorecard = build_scorecard(file_critiques)
        if args.output_format == "json":
            print(render_scorecard_json(scorecard))
        else:
            print(render_scorecard_human(scorecard))
    elif args.output_format == "json":
        print(format_results_json(results))
    elif args.output_format == "sarif":
        from eigenhelm.output.sarif import format_sarif

        print(format_sarif(results, tool_version=_get_tool_version()))
    elif getattr(args, "rank", False):
        print(
            format_ranking_human(
                results,
                bottom=getattr(args, "bottom", None),
                bottom_pct=getattr(args, "bottom_pct", None),
            )
        )
    else:
        classify = getattr(args, "classify", False)
        for path, resp in results:
            print(format_result_human(path, resp, classify=classify))
        if len(results) > 1:
            print(format_summary_human(results, classify=classify))


def _dispatch_evaluation(
    args: argparse.Namespace,
    helm: DynamicHelm,
    config,
    language: str | None,
) -> list[tuple[Path | str, EvaluationResponse]] | int:
    """Run the appropriate evaluation path. Returns results or error exit code."""
    top_n = getattr(args, "top_n", None)
    directive_threshold = getattr(args, "directive_threshold", None)
    attr_kwargs = {
        "top_n": top_n if top_n is not None else 3,
        "directive_threshold": directive_threshold
        if directive_threshold is not None
        else 0.3,
    }

    if not args.paths and args.diff_range is None:
        if not language:
            print(
                "ERROR: --language is required when reading from stdin", file=sys.stderr
            )
            return 3
        return _evaluate_stdin(helm, language, **attr_kwargs)
    if args.diff_range is not None:
        try:
            return _evaluate_diff_paths(
                helm, args.diff_range, config=config, **attr_kwargs
            )
        except RuntimeError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 3
    return _evaluate_paths(helm, args.paths, config=config, **attr_kwargs)


def main(argv: list[str] | None = None) -> int:
    """Entry point for eigenhelm-evaluate.

    Returns exit code: 0 (accepted), 1 (warned), 2 (rejected), 3 (error).
    """
    args = _build_parser().parse_args(argv)

    fmt_err = _resolve_format(args)
    if fmt_err is not None:
        return fmt_err

    try:
        config, _ = _load_project_config()

        model_path = args.model
        if model_path is None and config is not None and config.model:
            model_path = config.model
        if model_path is None:
            # Fall back to bundled default model
            from eigenhelm.trained_models import default_model_path

            model_path = str(default_model_path())
        language = args.language
        if language is None and config is not None and config.language:
            language = config.language
        strict = args.strict or (config is not None and config.strict)

        eigenspace = None
        if model_path:
            from eigenhelm.eigenspace import load_model

            eigenspace = load_model(model_path)

        # 015: Threshold hierarchy — CLI flags override model calibration.
        # DynamicHelm resolves: explicit args > model calibration > hardcoded 0.4/0.6.
        # Config file thresholds are applied post-evaluation via _apply_thresholds().
        helm = DynamicHelm(
            eigenspace=eigenspace,
            accept_threshold=args.accept_threshold,
            reject_threshold=args.reject_threshold,
        )
        results = _dispatch_evaluation(args, helm, config, language)
        if isinstance(results, int):
            return results
        if not results:
            return 0

        _render_output(results, args)
        return compute_exit_code(results, strict=strict, lenient=args.lenient)

    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())

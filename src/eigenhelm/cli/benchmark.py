"""eigenhelm-benchmark CLI — run real-world use case benchmarks.

Usage:
    eigenhelm-benchmark --project /path/to/project
    eigenhelm-benchmark --corpus corpora/usecase-benchmark.toml
    eigenhelm-benchmark --project /path/to/project --format json

Exit codes:
    0  Benchmark completed
    1  No evaluable files found
    2  Runtime error
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="eigenhelm-benchmark",
        description="Run real-world use case benchmarks against source projects",
    )
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument(
        "--project",
        type=Path,
        action="append",
        default=None,
        help="Project directory to evaluate (can be repeated)",
    )
    source_group.add_argument(
        "--corpus",
        type=Path,
        default=None,
        help="Path to TOML corpus manifest",
    )
    parser.add_argument("--model", default=None, help="Path to .npz eigenspace model")
    parser.add_argument(
        "--format",
        dest="output_format",
        choices=["human", "json"],
        default="human",
        help="Output format (default: human)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Save JSON report to this path",
    )
    parser.add_argument(
        "--good-corpus",
        dest="good_corpus",
        type=Path,
        default=None,
        help="Path to known-good corpus for FP analysis",
    )
    parser.add_argument(
        "--bad-corpus",
        dest="bad_corpus",
        type=Path,
        default=None,
        help="Path to known-problematic corpus for FN analysis",
    )
    parser.add_argument(
        "--replay",
        type=Path,
        default=None,
        help="Replay evaluation against recent commits of this git repo",
    )
    parser.add_argument(
        "--commits",
        type=int,
        default=50,
        help="Number of commits to replay (default: 50)",
    )
    parser.add_argument(
        "--compare",
        type=Path,
        default=None,
        help="Compare current run against a baseline JSON report",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point for eigenhelm-benchmark."""
    args = _build_parser().parse_args(argv)

    try:
        # Load model
        model_path = args.model
        if model_path is None:
            from eigenhelm.trained_models import default_model_path

            model_path = str(default_model_path())

        from eigenhelm.eigenspace import load_model
        from eigenhelm.helm import DynamicHelm

        eigenspace = load_model(model_path)
        helm = DynamicHelm(eigenspace=eigenspace)

        from eigenhelm.validation.usecase_benchmark import (
            UseCaseBenchmark,
            add_fp_fn_targets,
            add_replay_target,
            compare_reports,
            compute_fp_fn,
            compute_noise_rate,
            replay_commits,
            sync_corpus,
        )
        from eigenhelm.validation.usecase_models import QualityTarget

        corpus_version = ""
        project_list: list[tuple[Path, str | None, str]] = []

        if args.corpus:
            # Sync and register projects from manifest
            import tempfile

            corpus_dir = Path(tempfile.mkdtemp(prefix="eigenhelm-benchmark-"))
            import tomllib

            with open(args.corpus, "rb") as f:
                manifest = tomllib.load(f)
            corpus_version = manifest.get("meta", {}).get("version", "")
            projects = sync_corpus(args.corpus, corpus_dir)
            for project in projects:
                project_dir = corpus_dir / project["name"]
                project_list.append(
                    (project_dir, project.get("src_dir"), project["name"])
                )
        else:
            for project_path in args.project:
                project_list.append((project_path, None, project_path.name))

        benchmark = UseCaseBenchmark(
            helm=helm,
            model_name=Path(model_path).name,
            model_version=eigenspace.version,
            corpus_version=corpus_version,
        )
        for proj_dir, src_dir, name in project_list:
            benchmark.add_project(proj_dir, src_dir=src_dir, name=name)

        report = benchmark.run()

        # FP/FN analysis if corpora provided
        if args.good_corpus or args.bad_corpus:
            good_evals = []
            bad_evals = []
            if args.good_corpus:
                good_bench = UseCaseBenchmark(helm=helm)
                good_bench.add_project(args.good_corpus, name="good-corpus")
                good_report = good_bench.run()
                good_evals = list(good_report.file_evaluations)
            if args.bad_corpus:
                bad_bench = UseCaseBenchmark(helm=helm)
                bad_bench.add_project(args.bad_corpus, name="bad-corpus")
                bad_report = bad_bench.run()
                bad_evals = list(bad_report.file_evaluations)

            fp_rate, fn_rate = compute_fp_fn(good_evals, bad_evals, impl_only=True)
            report = add_fp_fn_targets(report, fp_rate, fn_rate)

        # Commit replay (US5)
        if args.replay:
            replays = replay_commits(args.replay, helm, n_commits=args.commits)
            noise_rate = compute_noise_rate(replays)
            report = add_replay_target(report, noise_rate)
            print(f"\nCommit Replay ({len(replays)} commits):", file=sys.stderr)
            print(f"  Noise rate: {noise_rate:.1%}", file=sys.stderr)
            total_flagged = sum(r.n_flagged for r in replays)
            total_fp = sum(r.n_false_positive for r in replays)
            print(
                f"  Total flagged: {total_flagged}, FP (non-impl): {total_fp}",
                file=sys.stderr,
            )

        if report.n_files == 0:
            print("ERROR: No evaluable files found", file=sys.stderr)
            return 1

        if args.output_format == "json":
            print(report.to_json())
        else:
            print(report.render())

        if args.compare:
            import json as _json

            baseline_data = _json.loads(args.compare.read_text())
            # Reconstruct minimal baseline for comparison (targets only)
            baseline_targets = tuple(
                QualityTarget(
                    name=t["name"],
                    description=t["description"],
                    baseline=t["baseline"],
                    target=t["target"],
                    direction=t["direction"],
                )
                for t in baseline_data.get("targets", [])
            )
            from dataclasses import replace as dc_replace2

            baseline = dc_replace2(report, targets=baseline_targets)
            alerts = compare_reports(report, baseline)
            if alerts:
                print(f"\nRegressions ({len(alerts)}):", file=sys.stderr)
                for alert in alerts:
                    print(f"  {alert.message}", file=sys.stderr)
            else:
                print("\nNo regressions detected.", file=sys.stderr)

        if args.output:
            report.save(args.output)
            print(f"\nReport saved to {args.output}", file=sys.stderr)

        return 0

    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

"""eigenhelm-harness CLI — compare two corpora with Mann-Whitney U test.

Usage:
    eigenhelm-harness --before corpus/before/ --after corpus/after/
    eigenhelm-harness --before before/ --after after/ --model model.npz --json

Exit codes:
    0  Harness completed (regardless of significance)
    1  One or both corpus directories empty/unreadable
    2  Runtime error
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from eigenhelm.harness.report import HarnessReport


def format_harness_human(report: HarnessReport) -> str:
    """Format a HarnessReport for human-readable output."""
    b = report.before
    a = report.after

    delta_symbol = "✓ Improvement" if report.improvement else "✗ No improvement"
    sig_symbol = "YES ✓" if report.significant else "NO ✗"

    lines = [
        "eigenhelm-harness: Quality Comparison Report",
        f"  Before corpus:  {b.n_files} files evaluated, {b.n_skipped} skipped",
        f"    Mean score:   {b.mean_score:.2f}  "
        f"(median: {b.median_score:.2f}, std: {b.std_score:.2f})",
        f"    Accept/Warn/Reject: {b.accepted} / {b.warned} / {b.rejected}",
        "",
        f"  After corpus:   {a.n_files} files evaluated, {a.n_skipped} skipped",
        f"    Mean score:   {a.mean_score:.2f}  "
        f"(median: {a.median_score:.2f}, std: {a.std_score:.2f})",
        f"    Accept/Warn/Reject: {a.accepted} / {a.warned} / {a.rejected}",
        "",
        f"  Delta (after − before):  {report.delta_mean_score:+.2f}  {delta_symbol}",
        f"  Mann-Whitney U:           {report.u_statistic:.1f}",
        f"  p-value:                  {report.p_value:.4f}",
        f"  Significant at α=0.05:    {sig_symbol}",
    ]
    return "\n".join(lines)


def format_harness_json(report: HarnessReport) -> str:
    """Format a HarnessReport as JSON matching field names exactly."""

    def _stats_dict(s):
        return {
            "n_files": s.n_files,
            "n_skipped": s.n_skipped,
            "mean_score": s.mean_score,
            "median_score": s.median_score,
            "std_score": s.std_score,
            "accepted": s.accepted,
            "warned": s.warned,
            "rejected": s.rejected,
        }

    output = {
        "before": _stats_dict(report.before),
        "after": _stats_dict(report.after),
        "delta_mean_score": report.delta_mean_score,
        "u_statistic": report.u_statistic,
        "p_value": report.p_value,
        "significant": report.significant,
        "improvement": report.improvement,
    }
    return json.dumps(output, indent=2)


def main(argv: list[str] | None = None) -> int:
    """Entry point for eigenhelm-harness.

    Returns exit code: 0 (success), 1 (empty corpus), 2 (runtime error).
    """
    parser = argparse.ArgumentParser(
        prog="eigenhelm-harness",
        description="Compare two corpora with statistical testing",
    )
    parser.add_argument("--before", required=True, type=Path, help="Before corpus directory")
    parser.add_argument("--after", required=True, type=Path, help="After corpus directory")
    parser.add_argument("--model", default=None, help="Path to .npz eigenspace model")
    parser.add_argument("--json", dest="json_output", action="store_true", help="JSON output")
    args = parser.parse_args(argv)

    try:
        eigenspace = None
        if args.model:
            from eigenhelm.eigenspace import load_model

            eigenspace = load_model(args.model)

        from eigenhelm.harness.runner import run_harness

        report = run_harness(args.before, args.after, eigenspace=eigenspace)

        if args.json_output:
            print(format_harness_json(report))
        else:
            print(format_harness_human(report))

        return 0

    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

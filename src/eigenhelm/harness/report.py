"""CorpusStats and HarnessReport frozen dataclasses plus formatters.

CorpusStats: aggregate statistics from evaluating one corpus directory.
HarnessReport: full output of the harness comparison (stats + significance test).
"""

from __future__ import annotations

import json
from dataclasses import dataclass


@dataclass(frozen=True)
class CorpusStats:
    """Aggregate statistics computed from evaluating one corpus directory."""

    n_files: int
    n_skipped: int
    mean_score: float
    median_score: float
    std_score: float
    accepted: int
    warned: int
    rejected: int
    scores: tuple[float, ...]


@dataclass(frozen=True)
class HarnessReport:
    """Full output of the eigenhelm-harness evaluation harness.

    delta_mean_score = after.mean_score - before.mean_score
    Negative delta = improvement (lower scores = better aesthetics).
    significant = p_value < 0.05
    improvement = significant AND delta_mean_score < 0.0
    """

    before: CorpusStats
    after: CorpusStats
    delta_mean_score: float
    u_statistic: float
    p_value: float
    significant: bool
    improvement: bool


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

"""Per-repository scorecard: M1-M5 mandatory checks + Q1-Q5 qualitative scores.

Produces structured quality reports from AestheticCritic evaluation results.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from eigenhelm.critic import Critique
from eigenhelm.critic.anti_patterns import AntiPatternViolation


@dataclass(frozen=True)
class ScorecardEntry:
    """Per-file scorecard entry."""

    file_path: str
    mandatory_checks: dict[str, bool]  # M1-M5: pass/fail
    qualitative_scores: dict[str, float]  # Q1-Q5: numeric [0, 1]
    anti_patterns: list[AntiPatternViolation] = field(default_factory=list)


@dataclass(frozen=True)
class ScorecardSummary:
    """Aggregate scorecard statistics."""

    total_files: int
    mandatory_pass_rates: dict[str, float]  # M1-M5 pass percentages
    qualitative_distributions: dict[str, dict[str, float]]  # Q1-Q5 mean/min/max
    anti_pattern_counts: dict[str, int]


@dataclass(frozen=True)
class Scorecard:
    """Complete repository scorecard."""

    entries: list[ScorecardEntry]
    summary: ScorecardSummary


# --- M1-M5 Mandatory Check Thresholds ---

M_CHECKS = {
    "M1_birkhoff": ("birkhoff_measure", ">", 0.8),
    "M2_compression_structure": ("compression_structure", "<", 0.5),
    "M3_compression_ratio": ("compression_ratio", "<", 0.8),
    "M4_shannon_entropy": ("shannon_entropy", "in", (3.5, 6.5)),
    "M5_ncd_exemplar": ("ncd_exemplar_distance", "<", 0.5),
}


def _check_mandatory(
    critique: Critique,
) -> dict[str, bool]:
    """Evaluate M1-M5 mandatory checks against a Critique."""
    # Build metrics lookup from directly available Critique data
    metrics: dict[str, float | None] = {
        "birkhoff_measure": critique.metrics.birkhoff_measure,
        "compression_ratio": critique.metrics.compression_ratio,
        "shannon_entropy": critique.metrics.entropy,
    }

    # Extract dimension raw values from top-N violations (may be incomplete)
    for v in critique.violations:
        metrics.setdefault(v.dimension, v.raw_value)

    # compression_structure fallback: birkhoff_measure directly (013 polarity)
    if "compression_structure" not in metrics:
        bm = critique.metrics.birkhoff_measure
        metrics["compression_structure"] = bm if bm is not None else None

    # NCD fallback: derive from contributions when NCD was computed but fell
    # out of top-N violations. contributions[dim] = normalized * weight, and
    # for NCD the normalized value equals the raw NCD distance.
    if "ncd_exemplar_distance" not in metrics:
        w = critique.score.weights.get("ncd_exemplar_distance", 0.0)
        contrib = critique.score.contributions.get("ncd_exemplar_distance")
        if w > 0.0 and contrib is not None:
            metrics["ncd_exemplar_distance"] = contrib / w

    results: dict[str, bool] = {}
    for check_name, (metric, op, threshold) in M_CHECKS.items():
        val = metrics.get(metric)
        if val is None:
            # Metric genuinely unavailable (e.g., NCD without exemplars)
            results[check_name] = True
            continue
        if op == ">":
            results[check_name] = val > threshold
        elif op == "<":
            results[check_name] = val < threshold
        elif op == "in":
            lo, hi = threshold
            results[check_name] = lo <= val <= hi
    return results


def _compute_qualitative(
    critique: Critique,
) -> dict[str, float]:
    """Compute Q1-Q5 qualitative scores from a Critique."""
    birkhoff = critique.metrics.birkhoff_measure
    entropy = critique.metrics.entropy
    overall = critique.score.value

    # Look up NCD from violations
    ncd_val = 0.0
    for v in critique.violations:
        if v.dimension == "ncd_exemplar_distance":
            ncd_val = v.raw_value if v.raw_value is not None else 0.0
            break

    return {
        "Q1_birkhoff": birkhoff if birkhoff is not None else 0.0,
        "Q2_compression_structure": birkhoff if birkhoff is not None else 0.0,
        "Q3_token_entropy": 1.0 - min((entropy if entropy is not None else 0.0) / 8.0, 1.0),
        "Q4_ncd_exemplar": ncd_val,
        "Q5_overall_aesthetic": overall,
    }


def build_entry(file_path: str, critique: Critique) -> ScorecardEntry:
    """Build a ScorecardEntry from a file path and its Critique."""
    return ScorecardEntry(
        file_path=file_path,
        mandatory_checks=_check_mandatory(critique),
        qualitative_scores=_compute_qualitative(critique),
        anti_patterns=list(critique.anti_patterns),
    )


def build_summary(entries: list[ScorecardEntry]) -> ScorecardSummary:
    """Aggregate ScorecardEntries into a summary."""
    n = len(entries)
    if n == 0:
        return ScorecardSummary(
            total_files=0,
            mandatory_pass_rates={},
            qualitative_distributions={},
            anti_pattern_counts={},
        )

    # M-check pass rates
    m_keys = list(M_CHECKS.keys())
    pass_rates = {
        k: sum(1 for e in entries if e.mandatory_checks.get(k, True)) / n
        for k in m_keys
    }

    # Q-score distributions
    q_keys = ["Q1_birkhoff", "Q2_compression_structure", "Q3_token_entropy",
              "Q4_ncd_exemplar", "Q5_overall_aesthetic"]
    distributions: dict[str, dict[str, float]] = {}
    for qk in q_keys:
        vals = [e.qualitative_scores.get(qk, 0.0) for e in entries]
        distributions[qk] = {
            "mean": sum(vals) / n,
            "min": min(vals),
            "max": max(vals),
        }

    # Anti-pattern counts
    ap_counts: dict[str, int] = {}
    for entry in entries:
        for ap in entry.anti_patterns:
            ap_counts[ap.pattern_name] = ap_counts.get(ap.pattern_name, 0) + 1

    return ScorecardSummary(
        total_files=n,
        mandatory_pass_rates=pass_rates,
        qualitative_distributions=distributions,
        anti_pattern_counts=ap_counts,
    )


def build_scorecard(
    file_critiques: list[tuple[str, Critique]],
) -> Scorecard:
    """Build a complete Scorecard from a list of (file_path, Critique) pairs."""
    entries = [build_entry(fp, c) for fp, c in file_critiques]
    summary = build_summary(entries)
    return Scorecard(entries=entries, summary=summary)


# --- Renderers ---


def render_human(scorecard: Scorecard) -> str:
    """Render scorecard as human-readable text."""
    lines: list[str] = []
    lines.append("═" * 60)
    lines.append("  EIGENHELM SCORECARD")
    lines.append("═" * 60)
    lines.append("")

    for entry in scorecard.entries:
        lines.append(f"📄 {entry.file_path}")

        # Mandatory checks
        for k, passed in entry.mandatory_checks.items():
            symbol = "✓" if passed else "✗"
            lines.append(f"  {symbol} {k}")

        # Qualitative scores
        for k, val in entry.qualitative_scores.items():
            lines.append(f"  {k}: {val:.3f}")

        # Anti-patterns
        if entry.anti_patterns:
            for ap in entry.anti_patterns:
                lines.append(f"  ⚠ {ap.pattern_name}: {ap.explanation}")
        lines.append("")

    # Summary
    s = scorecard.summary
    lines.append("─" * 60)
    lines.append(f"  Summary: {s.total_files} files")
    lines.append("")
    lines.append("  Mandatory Check Pass Rates:")
    for k, rate in s.mandatory_pass_rates.items():
        lines.append(f"    {k}: {rate:.0%}")
    lines.append("")
    lines.append("  Qualitative Score Distributions:")
    for k, dist in s.qualitative_distributions.items():
        lines.append(
            f"    {k}: mean={dist['mean']:.3f}"
            f" min={dist['min']:.3f} max={dist['max']:.3f}"
        )

    if s.anti_pattern_counts:
        lines.append("")
        lines.append("  Anti-Pattern Counts:")
        for name, count in s.anti_pattern_counts.items():
            lines.append(f"    {name}: {count}")

    lines.append("─" * 60)
    return "\n".join(lines)


def render_json(scorecard: Scorecard) -> str:
    """Render scorecard as JSON."""
    def _entry_dict(e: ScorecardEntry) -> dict[str, Any]:
        return {
            "file_path": e.file_path,
            "mandatory_checks": e.mandatory_checks,
            "qualitative_scores": e.qualitative_scores,
            "anti_patterns": [
                {"pattern_name": ap.pattern_name, "explanation": ap.explanation,
                 "triggering_metrics": ap.triggering_metrics}
                for ap in e.anti_patterns
            ],
        }

    output = {
        "entries": [_entry_dict(e) for e in scorecard.entries],
        "summary": {
            "total_files": scorecard.summary.total_files,
            "mandatory_pass_rates": scorecard.summary.mandatory_pass_rates,
            "qualitative_distributions": scorecard.summary.qualitative_distributions,
            "anti_pattern_counts": scorecard.summary.anti_pattern_counts,
        },
    }
    return json.dumps(output, indent=2)

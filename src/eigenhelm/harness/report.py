"""CorpusStats and HarnessReport frozen dataclasses.

CorpusStats: aggregate statistics from evaluating one corpus directory.
HarnessReport: full output of the harness comparison (stats + significance test).
"""

from __future__ import annotations

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

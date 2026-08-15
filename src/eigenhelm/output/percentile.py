"""Percentile computation and ranking from ScoreDistribution.

Provides quality percentile (higher = better) from the 7-point summary
stored in .npz models, plus relative file ranking for changeset review.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import TYPE_CHECKING

import numpy as np

from eigenhelm.output.models import (
    DimensionContribution,
    FileRanking,
    PercentileResult,
    RankedFile,
)

if TYPE_CHECKING:
    from eigenhelm.models import ScoreDistribution

__all__ = [
    "DimensionContribution",
    "FileRanking",
    "PercentileResult",
    "RankedFile",
    "compute_quality_percentile",
    "compute_ranking",
]


# ---------------------------------------------------------------------------
# Percentile computation
# ---------------------------------------------------------------------------


def compute_quality_percentile(
    score: float, distribution: ScoreDistribution | None
) -> PercentileResult:
    """Compute quality percentile from score and 7-point distribution.

    Uses numpy.interp for linear interpolation. Scores outside the
    distribution range are clamped. Quality percentile inverts the loss
    percentile so higher = better.

    Returns PercentileResult(available=False) when distribution is None.
    """
    if distribution is None:
        return PercentileResult(
            percentile=0.0, available=False, raw_loss_percentile=0.0
        )

    # 7-point summary: score values → loss percentiles
    xp = [
        distribution.min,
        distribution.p10,
        distribution.p25,
        distribution.median,
        distribution.p75,
        distribution.p90,
        distribution.max,
    ]
    fp = [0.0, 10.0, 25.0, 50.0, 75.0, 90.0, 100.0]

    # Guard against degenerate (flat) distributions where all points are equal.
    # np.interp gives pathological results at repeated x-values.
    if xp[0] == xp[-1]:
        # All scores identical — any score is at the median (p50)
        raw_loss_pct = 50.0
    else:
        raw_loss_pct = float(np.interp(score, xp, fp))
    quality_pct = 100.0 - raw_loss_pct

    return PercentileResult(
        percentile=quality_pct,
        available=True,
        raw_loss_percentile=raw_loss_pct,
    )


# ---------------------------------------------------------------------------
# Relative ranking
# ---------------------------------------------------------------------------


def compute_ranking(
    results: Sequence[tuple[str, float, float | None]],
    bottom: int | None = None,
    bottom_pct: float | None = None,
) -> FileRanking:
    """Rank files by score and highlight bottom performers.

    Args:
        results: List of (file_path, score, percentile_or_None).
        bottom: Explicit highlight count override.
        bottom_pct: Explicit highlight percentage override (0-100).

    Returns:
        FileRanking with files sorted best-first (lowest score).
    """
    count = len(results)
    if count == 0:
        return FileRanking(files=(), highlight_count=0, spread=0.0)

    # Sort by score ascending (best first)
    sorted_results = sorted(results, key=lambda r: r[1])

    # Compute highlight count
    if bottom is not None:
        highlight_n = bottom
    elif bottom_pct is not None:
        highlight_n = math.floor(count * bottom_pct / 100.0)
    else:
        highlight_n = min(3, math.floor(count * 0.20))

    highlight_n = max(0, min(highlight_n, count))

    scores = [s for _, s, _ in sorted_results]
    spread = scores[-1] - scores[0] if count > 1 else 0.0

    # Spec edge case: all identical scores → no outliers, highlight 0
    if spread == 0.0:
        actual_highlight = 0
    elif highlight_n > 0:
        # Resolve ties at the boundary: include all files sharing the
        # score of the last highlighted file
        cutoff_score = sorted_results[count - highlight_n][1]
        actual_highlight = sum(1 for _, s, _ in sorted_results if s >= cutoff_score)
    else:
        actual_highlight = 0

    ranked_files = tuple(
        RankedFile(
            file_path=fp,
            rank=i + 1,
            score=s,
            percentile=p,
            highlighted=(i >= count - actual_highlight),
        )
        for i, (fp, s, p) in enumerate(sorted_results)
    )

    return FileRanking(
        files=ranked_files,
        highlight_count=actual_highlight,
        spread=spread,
    )

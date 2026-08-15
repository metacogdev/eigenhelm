"""Data models for percentile computation and file ranking output."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DimensionContribution:
    """Per-dimension contribution to the total aesthetic loss.

    Surfaces normalized values from AestheticCritic scoring.
    """

    dimension: str
    normalized_value: float
    weight: float
    weighted_contribution: float


@dataclass(frozen=True)
class PercentileResult:
    """Result of percentile computation against training corpus distribution."""

    percentile: float  # Quality percentile 0-100 (higher = better)
    available: bool  # True if model had ScoreDistribution
    raw_loss_percentile: float  # Loss percentile 0-100 (lower = better)


@dataclass(frozen=True)
class RankedFile:
    """A single file in a ranking result."""

    file_path: str
    rank: int  # 1-based (1 = best)
    score: float
    percentile: float | None
    highlighted: bool


@dataclass(frozen=True)
class FileRanking:
    """Ranked set of files with highlight metadata."""

    files: tuple[RankedFile, ...]
    highlight_count: int
    spread: float  # score range (max - min)

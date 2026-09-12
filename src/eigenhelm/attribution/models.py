"""Data models for score attribution and directive generation.

All entities are frozen dataclasses following the project convention.
"""

from __future__ import annotations

from eigenhelm.attribution.constants import DEFAULT_TOP_N, DEFAULT_DIRECTIVE_THRESHOLD
from dataclasses import dataclass


@dataclass(frozen=True)
class FeatureContribution:
    """A single feature's contribution to a PCA-based dimension score."""

    feature_index: int
    feature_name: str
    contribution_value: float
    contribution_magnitude: float
    raw_value: float
    corpus_mean: float
    standardized_deviation: float
    rank: int


@dataclass(frozen=True)
class DirectAttribution:
    """Attribution for an information-theoretic dimension."""

    metric_name: str
    computed_value: float
    normalization: str
    normalized_score: float
    exemplar_id: str | None = None


@dataclass(frozen=True)
class SourceLocation:
    """Points to the evaluated code unit's location."""

    code_unit_name: str
    start_line: int
    end_line: int
    file_path: str | None = None


@dataclass(frozen=True)
class DimensionAttribution:
    """Full attribution breakdown for one scoring dimension."""

    dimension: str
    normalized_score: float
    available: bool
    method: str
    source_location: SourceLocation | None = None
    features: tuple[FeatureContribution, ...] = ()
    direct: DirectAttribution | None = None


@dataclass(frozen=True)
class Directive:
    """An actionable record combining attribution with guidance."""

    category: str
    dimension: str
    normalized_score: float
    attribution: DimensionAttribution
    source_location: SourceLocation
    severity: str


@dataclass(frozen=True)
class AttributionResult:
    """Top-level container for attribution output."""

    dimensions: tuple[DimensionAttribution, ...]
    directives: tuple[Directive, ...]
    top_n: int = DEFAULT_TOP_N
    directive_threshold: float = DEFAULT_DIRECTIVE_THRESHOLD
    vocabulary_version: str = "v1"

"""Pydantic I/O models for the HTTP API.

Thin serialization wrappers around the pipeline types — no business logic here.
"""

from __future__ import annotations

from eigenhelm.attribution.constants import DEFAULT_TOP_N, DEFAULT_DIRECTIVE_THRESHOLD
from pydantic import BaseModel, Field


class EvaluateRequest(BaseModel):
    """Input for POST /v1/evaluate."""

    source: str
    language: str
    file_path: str | None = None
    top_n: int = Field(
        default=DEFAULT_TOP_N, ge=1
    )  # 017: top features per PCA dimension
    directive_threshold: float = Field(
        default=0.3, ge=0.0, le=1.0
    )  # 017: minimum score for directives


class ViolationOut(BaseModel):
    """Serializable form of eigenhelm.critic.Violation."""

    dimension: str
    raw_value: float
    normalized_value: float
    contribution: float


class ContributionOut(BaseModel):
    """Serializable per-dimension contribution breakdown (016)."""

    dimension: str
    normalized_value: float
    weight: float
    weighted_contribution: float


class FeatureContributionOut(BaseModel):
    """Serializable form of attribution FeatureContribution (017)."""

    feature_index: int
    feature_name: str
    contribution_value: float
    contribution_magnitude: float
    raw_value: float
    corpus_mean: float
    standardized_deviation: float
    rank: int


class DirectAttributionOut(BaseModel):
    """Serializable form of attribution DirectAttribution (017)."""

    metric_name: str
    computed_value: float
    normalization: str
    normalized_score: float
    exemplar_id: str | None = None


class SourceLocationOut(BaseModel):
    """Serializable form of attribution SourceLocation (017)."""

    code_unit_name: str
    start_line: int
    end_line: int
    file_path: str | None = None


class DimensionAttributionOut(BaseModel):
    """Serializable form of attribution DimensionAttribution (017)."""

    dimension: str
    normalized_score: float
    available: bool
    method: str
    source_location: SourceLocationOut | None = None
    features: list[FeatureContributionOut] = Field(default_factory=list)
    direct: DirectAttributionOut | None = None


class DirectiveOut(BaseModel):
    """Serializable form of attribution Directive (017)."""

    category: str
    dimension: str
    normalized_score: float
    attribution: DimensionAttributionOut
    source_location: SourceLocationOut
    severity: str


class AttributionResultOut(BaseModel):
    """Serializable form of AttributionResult (017)."""

    dimensions: list[DimensionAttributionOut]
    directives: list[DirectiveOut] = Field(default_factory=list)
    top_n: int = DEFAULT_TOP_N
    directive_threshold: float = DEFAULT_DIRECTIVE_THRESHOLD
    vocabulary_version: str = "v1"


class RegionSpanOut(BaseModel):
    """Serializable line range for a region span (019)."""

    start_line: int
    end_line: int


class RegionSummaryOut(BaseModel):
    """Serializable region score decomposition (019)."""

    label: str
    spans: list[RegionSpanOut]
    total_lines: int
    score: float
    decision: str
    percentile: float | None = None


class EvaluateResponse(BaseModel):
    """Output for POST /v1/evaluate."""

    decision: str
    score: float
    structural_confidence: str
    violations: list[ViolationOut]
    warning: str | None = None
    file_path: str | None = None
    percentile: float | None = None
    percentile_available: bool = False
    contributions: list[ContributionOut] = Field(default_factory=list)
    attribution: AttributionResultOut | None = None
    regions: list[RegionSummaryOut] | None = None  # 019: test/production decomposition
    declaration_ratio: float | None = None  # 020: set when declaration-dominant


class FileEvalUnit(BaseModel):
    """One entry in a batch request."""

    source: str
    language: str
    file_path: str | None = None
    top_n: int = Field(default=DEFAULT_TOP_N, ge=1)
    directive_threshold: float = Field(
        default=DEFAULT_DIRECTIVE_THRESHOLD, ge=0.0, le=1.0
    )


class BatchRequest(BaseModel):
    """Input for POST /v1/evaluate/batch."""

    files: list[FileEvalUnit] = Field(min_length=1)


class BatchSummary(BaseModel):
    """Aggregate statistics over all files in a batch."""

    overall_decision: str
    total_files: int
    accepted: int
    warned: int
    rejected: int
    mean_score: float


class BatchResponse(BaseModel):
    """Output for POST /v1/evaluate/batch."""

    results: list[EvaluateResponse]
    summary: BatchSummary


class HealthResponse(BaseModel):
    """Output for GET /health."""

    status: str
    model_loaded: bool


class ReadyResponse(BaseModel):
    """Output for GET /ready."""

    status: str
    model_loaded: bool

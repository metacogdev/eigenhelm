"""Pydantic I/O models for the HTTP API.

Thin serialization wrappers around the pipeline types — no business logic here.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class EvaluateRequest(BaseModel):
    """Input for POST /v1/evaluate."""

    source: str
    language: str
    file_path: str | None = None
    top_n: int = Field(default=3, ge=1)  # 017: top features per PCA dimension
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
    top_n: int = 3
    directive_threshold: float = 0.3
    vocabulary_version: str = "v1"


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


class FileEvalUnit(BaseModel):
    """One entry in a batch request."""

    source: str
    language: str
    file_path: str | None = None
    top_n: int = Field(default=3, ge=1)
    directive_threshold: float = Field(default=0.3, ge=0.0, le=1.0)


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

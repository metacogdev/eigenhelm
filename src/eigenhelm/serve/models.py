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


class ViolationOut(BaseModel):
    """Serializable form of eigenhelm.critic.Violation."""

    dimension: str
    raw_value: float
    normalized_value: float
    contribution: float


class EvaluateResponse(BaseModel):
    """Output for POST /v1/evaluate."""

    decision: str
    score: float
    structural_confidence: str
    violations: list[ViolationOut]
    warning: str | None = None
    file_path: str | None = None


class FileEvalUnit(BaseModel):
    """One entry in a batch request."""

    source: str
    language: str
    file_path: str | None = None


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

"""POST /v1/evaluate and POST /v1/evaluate/batch routes.

All scoring logic lives in DynamicHelm — this layer is pure serialization.
"""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from eigenhelm.helm import DynamicHelm
from eigenhelm.helm.models import EvaluationRequest as HelmRequest
from eigenhelm.helm.models import EvaluationResponse as HelmResponse
from eigenhelm.serve.models import (
    AttributionResultOut,
    BatchRequest,
    BatchResponse,
    BatchSummary,
    ContributionOut,
    DimensionAttributionOut,
    DirectAttributionOut,
    DirectiveOut,
    EvaluateRequest,
    EvaluateResponse,
    FeatureContributionOut,
    SourceLocationOut,
    ViolationOut,
)

router = APIRouter(prefix="/v1")


def _map_response(
    helm_response: HelmResponse,
    file_path: str | None = None,
) -> EvaluateResponse:
    """Convert pipeline EvaluationResponse to Pydantic EvaluateResponse."""
    violations = [
        ViolationOut(
            dimension=v.dimension,
            raw_value=v.raw_value,
            normalized_value=v.normalized_value,
            contribution=v.contribution,
        )
        for v in helm_response.critique.violations
    ]
    contributions = [
        ContributionOut(
            dimension=c.dimension,
            normalized_value=c.normalized_value,
            weight=c.weight,
            weighted_contribution=c.weighted_contribution,
        )
        for c in helm_response.contributions
    ]
    # 017: Map attribution
    attribution_out = _map_attribution(helm_response.attribution)

    return EvaluateResponse(
        decision=helm_response.decision,
        score=helm_response.score,
        structural_confidence=helm_response.structural_confidence,
        violations=violations,
        warning=helm_response.warning,
        file_path=file_path,
        percentile=helm_response.percentile,
        percentile_available=helm_response.percentile_available,
        contributions=contributions,
        attribution=attribution_out,
    )


def _map_source_location(loc) -> SourceLocationOut | None:
    """Map attribution SourceLocation to Pydantic model."""
    if loc is None:
        return None
    return SourceLocationOut(
        code_unit_name=loc.code_unit_name,
        start_line=loc.start_line,
        end_line=loc.end_line,
        file_path=loc.file_path,
    )


def _map_dimension(dim) -> DimensionAttributionOut:
    """Map attribution DimensionAttribution to Pydantic model."""
    features = [
        FeatureContributionOut(
            feature_index=f.feature_index,
            feature_name=f.feature_name,
            contribution_value=f.contribution_value,
            contribution_magnitude=f.contribution_magnitude,
            raw_value=f.raw_value,
            corpus_mean=f.corpus_mean,
            standardized_deviation=f.standardized_deviation,
            rank=f.rank,
        )
        for f in dim.features
    ]
    direct = None
    if dim.direct is not None:
        direct = DirectAttributionOut(
            metric_name=dim.direct.metric_name,
            computed_value=dim.direct.computed_value,
            normalization=dim.direct.normalization,
            normalized_score=dim.direct.normalized_score,
            exemplar_id=dim.direct.exemplar_id,
        )
    return DimensionAttributionOut(
        dimension=dim.dimension,
        normalized_score=dim.normalized_score,
        available=dim.available,
        method=dim.method,
        source_location=_map_source_location(dim.source_location),
        features=features,
        direct=direct,
    )


def _map_attribution(attr) -> AttributionResultOut | None:
    """Map AttributionResult to Pydantic model."""
    if attr is None:
        return None
    dimensions = [_map_dimension(d) for d in attr.dimensions]
    directives = [
        DirectiveOut(
            category=d.category,
            dimension=d.dimension,
            normalized_score=d.normalized_score,
            attribution=_map_dimension(d.attribution),
            source_location=SourceLocationOut(
                code_unit_name=d.source_location.code_unit_name,
                start_line=d.source_location.start_line,
                end_line=d.source_location.end_line,
                file_path=d.source_location.file_path,
            ),
            severity=d.severity,
        )
        for d in attr.directives
    ]
    return AttributionResultOut(
        dimensions=dimensions,
        directives=directives,
        top_n=attr.top_n,
        directive_threshold=attr.directive_threshold,
        vocabulary_version=attr.vocabulary_version,
    )


def _compute_summary(results: list[EvaluateResponse]) -> BatchSummary:
    """Compute aggregate statistics from a list of per-file results."""
    accepted = sum(1 for r in results if r.decision == "accept")
    warned = sum(1 for r in results if r.decision == "warn")
    rejected = sum(1 for r in results if r.decision == "reject")
    total = len(results)
    mean_score = sum(r.score for r in results) / total if total > 0 else 0.0

    if rejected > 0:
        overall = "reject"
    elif warned > 0:
        overall = "warn"
    else:
        overall = "accept"

    return BatchSummary(
        overall_decision=overall,
        total_files=total,
        accepted=accepted,
        warned=warned,
        rejected=rejected,
        mean_score=mean_score,
    )


@router.post("/evaluate", response_model=EvaluateResponse)
def evaluate_single(payload: EvaluateRequest, request: Request) -> EvaluateResponse:
    """Evaluate a single code block through the full Stage 1→2→3 pipeline."""
    helm: DynamicHelm = request.app.state._helm
    result = helm.evaluate(
        HelmRequest(
            source=payload.source,
            language=payload.language,
            file_path=payload.file_path,
            top_n=payload.top_n,
            directive_threshold=payload.directive_threshold,
        )
    )
    return _map_response(result, file_path=payload.file_path)


@router.post("/evaluate/batch", response_model=BatchResponse)
def evaluate_batch(
    payload: BatchRequest, request: Request
) -> BatchResponse | JSONResponse:
    """Evaluate multiple code blocks. Sequential processing, order preserved."""
    helm: DynamicHelm = request.app.state._helm
    max_body_bytes = getattr(request.app.state, "_max_body_bytes", 1_048_576)

    results: list[EvaluateResponse] = []
    for entry in payload.files:
        # Per-file size validation
        if len(entry.source.encode("utf-8")) > max_body_bytes:
            return JSONResponse(
                status_code=413,
                content={
                    "error": "request_too_large",
                    "detail": f"file '{entry.file_path}' exceeds {max_body_bytes} byte limit",
                },
            )
        result = helm.evaluate(
            HelmRequest(
                source=entry.source,
                language=entry.language,
                file_path=entry.file_path,
                top_n=entry.top_n,
                directive_threshold=entry.directive_threshold,
            )
        )
        results.append(_map_response(result, file_path=entry.file_path))

    return BatchResponse(results=results, summary=_compute_summary(results))

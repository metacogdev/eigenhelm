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
    BatchRequest,
    BatchResponse,
    BatchSummary,
    EvaluateRequest,
    EvaluateResponse,
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
    return EvaluateResponse(
        decision=helm_response.decision,
        score=helm_response.score,
        structural_confidence=helm_response.structural_confidence,
        violations=violations,
        warning=helm_response.warning,
        file_path=file_path,
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
        )
    )
    return _map_response(result, file_path=payload.file_path)


@router.post("/evaluate/batch", response_model=BatchResponse)
def evaluate_batch(payload: BatchRequest, request: Request) -> BatchResponse | JSONResponse:
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
            )
        )
        results.append(_map_response(result, file_path=entry.file_path))

    return BatchResponse(results=results, summary=_compute_summary(results))

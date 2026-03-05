"""GET /health and GET /ready routes.

Health and readiness probes are unversioned (no /v1 prefix).
/health always returns 200 (liveness).
/ready returns 200 when server is ready, 503 when starting.
"""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from eigenhelm.serve.models import HealthResponse, ReadyResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    """Liveness probe — always 200 when process is alive."""
    model_loaded = getattr(request.app.state, "_model_loaded", False)
    return HealthResponse(status="healthy", model_loaded=model_loaded)


@router.get("/ready", response_model=ReadyResponse)
def ready(request: Request) -> JSONResponse | ReadyResponse:
    """Readiness probe — 200 when ready, 503 during startup."""
    model_loaded = getattr(request.app.state, "_model_loaded", False)
    helm = getattr(request.app.state, "_helm", None)
    if helm is None:
        # Lifespan hasn't completed yet
        return JSONResponse(
            status_code=503,
            content={"status": "starting", "model_loaded": False},
        )
    return ReadyResponse(status="ready", model_loaded=model_loaded)

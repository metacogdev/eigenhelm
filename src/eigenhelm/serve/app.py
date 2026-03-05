"""FastAPI application factory and lifespan context manager.

Usage:
    from eigenhelm.serve import create_app
    app = create_app(eigenspace=model)  # or create_app() for low-confidence

The factory creates a single DynamicHelm instance shared across all requests.
No file I/O is performed when eigenspace is provided directly.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from eigenhelm.helm import DynamicHelm
from eigenhelm.serve.middleware.size_limit import ContentSizeLimitMiddleware
from eigenhelm.serve.middleware.timeout import TimeoutMiddleware

if TYPE_CHECKING:
    from eigenhelm.models import EigenspaceModel


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Lifespan context manager — creates DynamicHelm on startup, clears on shutdown."""
    eigenspace = getattr(app.state, "_eigenspace", None)
    accept_threshold = getattr(app.state, "_accept_threshold", 0.4)
    reject_threshold = getattr(app.state, "_reject_threshold", 0.6)

    app.state._helm = DynamicHelm(
        eigenspace=eigenspace,
        accept_threshold=accept_threshold,
        reject_threshold=reject_threshold,
    )
    app.state._model_loaded = eigenspace is not None
    yield
    app.state._helm = None


def create_app(
    eigenspace: EigenspaceModel | None = None,
    accept_threshold: float = 0.4,
    reject_threshold: float = 0.6,
    max_body_bytes: int = 1_048_576,
    max_batch_bytes: int = 10_485_760,
    timeout_seconds: float = 30.0,
) -> FastAPI:
    """Create and return a configured FastAPI application.

    No I/O is performed inside this function — the eigenspace model is
    injected by the caller (pre-loaded via eigenhelm.eigenspace.load_model()).
    """
    app = FastAPI(title="eigenhelm", lifespan=_lifespan)

    # Store config on app.state for lifespan to read
    app.state._eigenspace = eigenspace
    app.state._accept_threshold = accept_threshold
    app.state._reject_threshold = reject_threshold
    app.state._max_body_bytes = max_body_bytes

    # Mount middleware (outermost applied first)
    # Timeout middleware only applies to /v1/* routes
    app.add_middleware(TimeoutMiddleware, timeout_seconds=timeout_seconds)
    # Size limit middleware — use batch limit for the overall request
    app.add_middleware(ContentSizeLimitMiddleware, max_bytes=max_batch_bytes)

    # Import and register routers
    from eigenhelm.serve.routes.evaluate import router as evaluate_router
    from eigenhelm.serve.routes.health import router as health_router

    app.include_router(health_router)
    app.include_router(evaluate_router)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"error": "validation_error", "detail": exc.errors()},
        )

    return app

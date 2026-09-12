"""Stage 5 — FastAPI sidecar application for agent integration."""

DEFAULT_MAX_BODY_BYTES: int = 1_048_576

from eigenhelm.serve.app import create_app  # noqa: E402

__all__ = ["create_app", "DEFAULT_MAX_BODY_BYTES"]

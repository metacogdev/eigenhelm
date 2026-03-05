"""TimeoutMiddleware — per-request timeout using anyio.fail_after.

Only applies to /v1/* routes. Health and readiness probes are excluded.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import anyio


class TimeoutMiddleware:
    """Pure ASGI middleware applying per-request timeouts.

    Excludes /health and /ready (non-/v1) paths from timeout enforcement.
    """

    def __init__(self, app: Any, timeout_seconds: float = 30.0) -> None:
        self.app = app
        self.timeout_seconds = timeout_seconds

    async def __call__(
        self,
        scope: dict[str, Any],
        receive: Callable,
        send: Callable,
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path: str = scope.get("path", "")
        # Only apply timeout to /v1/* routes
        if not path.startswith("/v1/"):
            await self.app(scope, receive, send)
            return

        try:
            with anyio.fail_after(self.timeout_seconds):
                await self.app(scope, receive, send)
        except TimeoutError:
            body = json.dumps(
                {
                    "error": "evaluation_timeout",
                    "detail": f"Processing exceeded {self.timeout_seconds}s timeout",
                }
            ).encode("utf-8")
            await send(
                {
                    "type": "http.response.start",
                    "status": 504,
                    "headers": [
                        [b"content-type", b"application/json"],
                        [b"content-length", str(len(body)).encode()],
                    ],
                }
            )
            await send({"type": "http.response.body", "body": body})

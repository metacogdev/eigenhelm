"""ContentSizeLimitMiddleware — pure ASGI body size enforcement.

Does NOT use BaseHTTPMiddleware (ContextVar propagation issues).
Wraps receive() to count body bytes and returns HTTP 413 on limit exceeded.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any


async def _send_413(send_fn: Callable, max_bytes: int) -> None:
    """Send a 413 Payload Too Large response."""
    body = json.dumps(
        {
            "error": "request_too_large",
            "detail": f"Request body exceeds {max_bytes} byte limit",
        }
    ).encode("utf-8")
    await send_fn(
        {
            "type": "http.response.start",
            "status": 413,
            "headers": [
                [b"content-type", b"application/json"],
                [b"content-length", str(len(body)).encode()],
            ],
        }
    )
    await send_fn({"type": "http.response.body", "body": body})


class ContentSizeLimitMiddleware:
    """Pure ASGI middleware enforcing request body size limits."""

    def __init__(self, app: Any, max_bytes: int = 1_048_576) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(
        self,
        scope: dict[str, Any],
        receive: Callable,
        send: Callable,
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        await self._handle_http(scope, receive, send)

    async def _handle_http(
        self,
        scope: dict[str, Any],
        receive: Callable,
        send: Callable,
    ) -> None:
        total = 0
        exceeded = False

        async def limited_receive() -> dict[str, Any]:
            nonlocal total, exceeded
            message = await receive()
            if message["type"] == "http.request":
                body = message.get("body", b"")
                total += len(body)
                if total > self.max_bytes:
                    exceeded = True
            return message

        response_started = False

        async def guarded_send(message: dict[str, Any]) -> None:
            nonlocal response_started
            if exceeded and not response_started:
                return  # suppress app's response; we'll send 413
            response_started = True
            await send(message)

        try:
            await self.app(scope, limited_receive, guarded_send)
        except Exception:
            if not exceeded:
                raise

        if exceeded and not response_started:
            await _send_413(send, self.max_bytes)

"""Minimal JSON-RPC 2.0 over stdio for MCP.

Handles framing (Content-Length headers), request parsing, and response
serialization. No external dependencies.
"""

from __future__ import annotations

import json
import sys
from typing import Any


def read_message(stream=None) -> dict[str, Any] | None:
    """Read one JSON-RPC message from stdin using Content-Length framing.

    Returns None on EOF.
    """
    if stream is None:
        stream = sys.stdin.buffer

    # Read headers until blank line
    content_length = None
    while True:
        line = stream.readline()
        if not line:
            return None  # EOF
        line_str = line.decode("utf-8", errors="replace").rstrip("\r\n")
        if line_str == "":
            break
        if line_str.lower().startswith("content-length:"):
            content_length = int(line_str.split(":", 1)[1].strip())

    if content_length is None:
        return None

    body = stream.read(content_length)
    if len(body) < content_length:
        return None  # Truncated

    return json.loads(body.decode("utf-8"))


def write_message(msg: dict[str, Any], stream=None) -> None:
    """Write one JSON-RPC message to stdout with Content-Length framing."""
    if stream is None:
        stream = sys.stdout.buffer

    body = json.dumps(msg).encode("utf-8")
    header = f"Content-Length: {len(body)}\r\n\r\n".encode("utf-8")
    stream.write(header + body)
    stream.flush()


def make_response(id: Any, result: Any) -> dict[str, Any]:
    """Build a JSON-RPC 2.0 success response."""
    return {"jsonrpc": "2.0", "id": id, "result": result}


def make_error(id: Any, code: int, message: str, data: Any = None) -> dict[str, Any]:
    """Build a JSON-RPC 2.0 error response."""
    error: dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return {"jsonrpc": "2.0", "id": id, "error": error}


# Standard JSON-RPC error codes
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603

"""MCP server — stdio JSON-RPC 2.0 event loop.

Loads the default model on startup, dispatches MCP protocol messages
to tool handlers, and manages server state (active model, helm instance).
"""

from __future__ import annotations

import importlib.metadata
import sys
from dataclasses import dataclass
from typing import Any

from eigenhelm.mcp.protocol import (
    INVALID_PARAMS,
    METHOD_NOT_FOUND,
    make_error,
    make_response,
    read_message,
    write_message,
)
from eigenhelm.mcp.tools import TOOL_DEFINITIONS, TOOL_HANDLERS


@dataclass
class ServerState:
    """Mutable state shared across tool invocations."""

    helm: Any = None  # DynamicHelm instance
    active_model_name: str | None = None


def _get_version() -> str:
    try:
        return importlib.metadata.version("eigenhelm")
    except importlib.metadata.PackageNotFoundError:
        return "0.0.0"


class McpServer:
    """MCP server implementing initialize, tools/list, and tools/call."""

    def __init__(self, model_path: str | None = None) -> None:
        self.state = ServerState()
        self._load_default_model(model_path)

    def _load_default_model(self, model_path: str | None) -> None:
        """Load the initial model into the helm."""
        from eigenhelm.helm import DynamicHelm

        eigenspace = None
        name = None

        if model_path:
            from eigenhelm.eigenspace import load_model

            eigenspace = load_model(model_path)
            from pathlib import Path

            name = Path(model_path).stem
        else:
            # Try project config first
            try:
                from pathlib import Path

                from eigenhelm.config import find_config, load_config

                cfg_path = find_config(Path.cwd())
                if cfg_path is not None:
                    config = load_config(cfg_path)
                    if config.model:
                        from eigenhelm.eigenspace import load_model

                        eigenspace = load_model(config.model)
                        name = Path(config.model).stem
            except Exception:
                pass

            # Fall back to bundled default
            if eigenspace is None:
                try:
                    from eigenhelm.eigenspace import load_model
                    from eigenhelm.trained_models import default_model_path

                    path = default_model_path()
                    eigenspace = load_model(str(path))
                    name = path.stem
                except Exception:
                    pass

        self.state.helm = DynamicHelm(eigenspace=eigenspace)
        self.state.active_model_name = name

    def handle_message(self, msg: dict[str, Any]) -> dict[str, Any] | None:
        """Dispatch a single JSON-RPC message. Returns response or None for notifications."""
        method = msg.get("method", "")
        msg_id = msg.get("id")
        params = msg.get("params", {})

        # Notifications (no id) — just acknowledge silently
        if msg_id is None:
            return None

        if method == "initialize":
            return self._handle_initialize(msg_id, params)
        elif method == "tools/list":
            return self._handle_tools_list(msg_id)
        elif method == "tools/call":
            return self._handle_tools_call(msg_id, params)
        elif method == "ping":
            return make_response(msg_id, {})
        else:
            return make_error(msg_id, METHOD_NOT_FOUND, f"Unknown method: {method}")

    def _handle_initialize(self, msg_id: Any, params: dict) -> dict[str, Any]:
        return make_response(
            msg_id,
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                },
                "serverInfo": {
                    "name": "eigenhelm",
                    "version": _get_version(),
                },
            },
        )

    def _handle_tools_list(self, msg_id: Any) -> dict[str, Any]:
        return make_response(msg_id, {"tools": TOOL_DEFINITIONS})

    def _handle_tools_call(self, msg_id: Any, params: dict) -> dict[str, Any]:
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})

        handler = TOOL_HANDLERS.get(tool_name)
        if handler is None:
            return make_error(
                msg_id,
                INVALID_PARAMS,
                f"Unknown tool: {tool_name}",
            )

        try:
            content = handler(self.state, arguments)
            return make_response(msg_id, {"content": content})
        except (ValueError, TypeError, KeyError) as exc:
            return make_response(
                msg_id,
                {
                    "content": [{"type": "text", "text": f"Error: {exc}"}],
                    "isError": True,
                },
            )
        except Exception as exc:
            return make_response(
                msg_id,
                {
                    "content": [{"type": "text", "text": f"Internal error: {exc}"}],
                    "isError": True,
                },
            )


def run_server(model_path: str | None = None) -> None:
    """Run the MCP server, reading from stdin and writing to stdout.

    Blocks until EOF on stdin.
    """
    server = McpServer(model_path=model_path)

    # Log to stderr so it doesn't interfere with protocol
    print(
        f"eigenhelm MCP server started (model: {server.state.active_model_name or 'none'})",
        file=sys.stderr,
    )

    while True:
        msg = read_message()
        if msg is None:
            break

        response = server.handle_message(msg)
        if response is not None:
            write_message(response)

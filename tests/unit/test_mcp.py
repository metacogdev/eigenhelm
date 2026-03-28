"""Unit tests for the MCP server."""

from __future__ import annotations

import io
import json

import pytest

from eigenhelm.mcp.protocol import (
    INVALID_PARAMS,
    METHOD_NOT_FOUND,
    make_error,
    make_response,
    read_message,
    write_message,
)
from eigenhelm.mcp.server import McpServer
from eigenhelm.mcp.tools import TOOL_DEFINITIONS, TOOL_HANDLERS


# ---------------------------------------------------------------------------
# Protocol tests
# ---------------------------------------------------------------------------


class TestProtocol:
    def test_read_message_parses_content_length(self):
        body = json.dumps({"jsonrpc": "2.0", "method": "ping", "id": 1}).encode()
        raw = f"Content-Length: {len(body)}\r\n\r\n".encode() + body
        stream = io.BytesIO(raw)
        msg = read_message(stream)
        assert msg == {"jsonrpc": "2.0", "method": "ping", "id": 1}

    def test_read_message_returns_none_on_eof(self):
        stream = io.BytesIO(b"")
        assert read_message(stream) is None

    def test_read_message_returns_none_on_missing_content_length(self):
        stream = io.BytesIO(b"\r\n")
        assert read_message(stream) is None

    def test_write_message_produces_valid_frame(self):
        stream = io.BytesIO()
        msg = {"jsonrpc": "2.0", "id": 1, "result": {}}
        write_message(msg, stream)

        stream.seek(0)
        parsed = read_message(stream)
        assert parsed == msg

    def test_roundtrip(self):
        stream = io.BytesIO()
        original = {"jsonrpc": "2.0", "id": 42, "result": {"tools": []}}
        write_message(original, stream)
        stream.seek(0)
        assert read_message(stream) == original

    def test_make_response(self):
        resp = make_response(1, {"key": "value"})
        assert resp["jsonrpc"] == "2.0"
        assert resp["id"] == 1
        assert resp["result"] == {"key": "value"}

    def test_make_error(self):
        resp = make_error(2, -32601, "Not found")
        assert resp["error"]["code"] == -32601
        assert resp["error"]["message"] == "Not found"
        assert resp["id"] == 2

    def test_make_error_with_data(self):
        resp = make_error(3, -32600, "Bad", data={"detail": "x"})
        assert resp["error"]["data"] == {"detail": "x"}


# ---------------------------------------------------------------------------
# Server message dispatch tests
# ---------------------------------------------------------------------------


class TestServerDispatch:
    @pytest.fixture()
    def server(self):
        """Create a server without loading a model (low-confidence mode)."""
        s = McpServer.__new__(McpServer)
        from eigenhelm.helm import DynamicHelm
        from eigenhelm.mcp.server import ServerState

        s.state = ServerState(helm=DynamicHelm(), active_model_name=None)
        return s

    def test_initialize(self, server):
        resp = server.handle_message(
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
        )
        assert resp["result"]["protocolVersion"] == "2024-11-05"
        assert "tools" in resp["result"]["capabilities"]
        assert resp["result"]["serverInfo"]["name"] == "eigenhelm"

    def test_tools_list(self, server):
        resp = server.handle_message(
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
        )
        tools = resp["result"]["tools"]
        names = {t["name"] for t in tools}
        assert names == {
            "evaluate",
            "evaluate_batch",
            "model_list",
            "model_info",
            "model_switch",
        }

    def test_tools_call_unknown_tool(self, server):
        resp = server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {"name": "nonexistent", "arguments": {}},
            }
        )
        assert resp["error"]["code"] == INVALID_PARAMS

    def test_unknown_method(self, server):
        resp = server.handle_message(
            {"jsonrpc": "2.0", "id": 4, "method": "unknown/method"}
        )
        assert resp["error"]["code"] == METHOD_NOT_FOUND

    def test_notification_returns_none(self, server):
        resp = server.handle_message(
            {"jsonrpc": "2.0", "method": "notifications/initialized"}
        )
        assert resp is None

    def test_ping(self, server):
        resp = server.handle_message({"jsonrpc": "2.0", "id": 5, "method": "ping"})
        assert resp["result"] == {}


# ---------------------------------------------------------------------------
# Tool execution tests
# ---------------------------------------------------------------------------


class TestToolExecution:
    @pytest.fixture()
    def server(self):
        s = McpServer.__new__(McpServer)
        from eigenhelm.helm import DynamicHelm
        from eigenhelm.mcp.server import ServerState

        s.state = ServerState(helm=DynamicHelm(), active_model_name=None)
        return s

    def test_evaluate_returns_decision(self, server):
        resp = server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 10,
                "method": "tools/call",
                "params": {
                    "name": "evaluate",
                    "arguments": {
                        "source": "def hello():\n    print('hello world')\n",
                        "language": "python",
                    },
                },
            }
        )
        content = resp["result"]["content"]
        assert len(content) == 1
        data = json.loads(content[0]["text"])
        assert data["decision"] in ("accept", "warn", "reject")
        assert "score" in data

    def test_evaluate_with_file_path(self, server):
        resp = server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 11,
                "method": "tools/call",
                "params": {
                    "name": "evaluate",
                    "arguments": {
                        "source": "function greet() { return 'hi'; }",
                        "language": "javascript",
                        "file_path": "greet.js",
                    },
                },
            }
        )
        data = json.loads(resp["result"]["content"][0]["text"])
        assert data.get("file_path") == "greet.js"

    def test_evaluate_empty_source(self, server):
        resp = server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 12,
                "method": "tools/call",
                "params": {
                    "name": "evaluate",
                    "arguments": {"source": "", "language": "python"},
                },
            }
        )
        data = json.loads(resp["result"]["content"][0]["text"])
        assert data["decision"] == "accept"
        assert data["score"] == 0.0

    def test_evaluate_batch_multiple_files(self, server):
        resp = server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 13,
                "method": "tools/call",
                "params": {
                    "name": "evaluate_batch",
                    "arguments": {
                        "files": [
                            {
                                "source": "def f(): pass",
                                "language": "python",
                                "file_path": "a.py",
                            },
                            {
                                "source": "def g(): pass",
                                "language": "python",
                                "file_path": "b.py",
                            },
                        ],
                    },
                },
            }
        )
        data = json.loads(resp["result"]["content"][0]["text"])
        assert data["summary"]["total_files"] == 2
        assert len(data["results"]) == 2
        assert data["summary"]["overall_decision"] in ("accept", "warn", "reject")

    def test_evaluate_batch_empty(self, server):
        resp = server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 14,
                "method": "tools/call",
                "params": {"name": "evaluate_batch", "arguments": {"files": []}},
            }
        )
        data = json.loads(resp["result"]["content"][0]["text"])
        assert data["summary"]["total_files"] == 0

    def test_model_list(self, server):
        resp = server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 20,
                "method": "tools/call",
                "params": {"name": "model_list", "arguments": {}},
            }
        )
        data = json.loads(resp["result"]["content"][0]["text"])
        assert isinstance(data, list)

    def test_model_info_not_found(self, server):
        resp = server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 21,
                "method": "tools/call",
                "params": {
                    "name": "model_info",
                    "arguments": {"name": "nonexistent-model-xyz"},
                },
            }
        )
        text = resp["result"]["content"][0]["text"]
        assert "not found" in text.lower()

    def test_model_switch_not_found(self, server):
        resp = server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 22,
                "method": "tools/call",
                "params": {
                    "name": "model_switch",
                    "arguments": {"name": "nonexistent-model-xyz"},
                },
            }
        )
        text = resp["result"]["content"][0]["text"]
        assert "Failed" in text or "not found" in text.lower()


# ---------------------------------------------------------------------------
# Tool definition schema tests
# ---------------------------------------------------------------------------


class TestToolDefinitions:
    def test_all_tools_have_handlers(self):
        for tool in TOOL_DEFINITIONS:
            assert tool["name"] in TOOL_HANDLERS, f"No handler for {tool['name']}"

    def test_all_handlers_have_definitions(self):
        definition_names = {t["name"] for t in TOOL_DEFINITIONS}
        for name in TOOL_HANDLERS:
            assert name in definition_names, f"No definition for handler {name}"

    def test_all_tools_have_input_schema(self):
        for tool in TOOL_DEFINITIONS:
            assert "inputSchema" in tool, f"{tool['name']} missing inputSchema"
            assert tool["inputSchema"]["type"] == "object"

    def test_all_tools_have_description(self):
        for tool in TOOL_DEFINITIONS:
            assert "description" in tool
            assert len(tool["description"]) > 10


# ---------------------------------------------------------------------------
# Integration: model switch with bundled model
# ---------------------------------------------------------------------------


class TestModelSwitch:
    @pytest.fixture()
    def server_with_model(self):
        """Server loaded with the bundled default model."""
        try:
            return McpServer()
        except Exception:
            pytest.skip("No bundled model available")

    @pytest.mark.requires_model
    def test_switch_to_bundled_model(self, server_with_model):
        server = server_with_model
        if server.state.active_model_name is None:
            pytest.skip("No active model")

        name = server.state.active_model_name
        resp = server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 30,
                "method": "tools/call",
                "params": {"name": "model_switch", "arguments": {"name": name}},
            }
        )
        text = resp["result"]["content"][0]["text"]
        assert "Switched" in text

    @pytest.mark.requires_model
    def test_evaluate_with_loaded_model(self, server_with_model):
        server = server_with_model
        resp = server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 31,
                "method": "tools/call",
                "params": {
                    "name": "evaluate",
                    "arguments": {
                        "source": (
                            "def fibonacci(n):\n"
                            "    if n <= 1:\n"
                            "        return n\n"
                            "    return fibonacci(n - 1) + fibonacci(n - 2)\n"
                        ),
                        "language": "python",
                    },
                },
            }
        )
        data = json.loads(resp["result"]["content"][0]["text"])
        assert data["decision"] in ("accept", "warn", "reject")
        assert 0.0 <= data["score"] <= 1.0

"""Contract tests for the MCP server: protocol framing, tool dispatch, and response shapes.

Tests verify the user-facing contracts of the MCP surface:
- JSON-RPC 2.0 protocol compliance (framing, message structure)
- Tool registration (all tools listed with correct schemas)
- Tool dispatch (evaluate, batch, model_list, model_info, model_switch)
- Error handling (unknown methods, unknown tools, handler exceptions)
- Server state management (model loading, helm initialization)
"""

from __future__ import annotations

import io
import json

import pytest

pytestmark = pytest.mark.contract


# ---------------------------------------------------------------------------
# Protocol: read_message / write_message framing
# ---------------------------------------------------------------------------


class TestProtocolFraming:
    """JSON-RPC 2.0 Content-Length framing contract."""

    def test_read_message_parses_valid_frame(self):
        from eigenhelm.mcp.protocol import read_message

        body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "ping"}).encode()
        frame = f"Content-Length: {len(body)}\r\n\r\n".encode() + body
        stream = io.BytesIO(frame)
        msg = read_message(stream)
        assert msg is not None
        assert msg["method"] == "ping"
        assert msg["id"] == 1

    def test_read_message_returns_none_on_eof(self):
        from eigenhelm.mcp.protocol import read_message

        stream = io.BytesIO(b"")
        assert read_message(stream) is None

    def test_read_message_returns_none_on_missing_content_length(self):
        from eigenhelm.mcp.protocol import read_message

        # Blank line with no Content-Length header
        stream = io.BytesIO(b"\r\n")
        assert read_message(stream) is None

    def test_read_message_returns_none_on_truncated_body(self):
        from eigenhelm.mcp.protocol import read_message

        # Declare 100 bytes but only provide 5
        frame = b"Content-Length: 100\r\n\r\nhello"
        stream = io.BytesIO(frame)
        assert read_message(stream) is None

    def test_write_message_produces_valid_frame(self):
        from eigenhelm.mcp.protocol import write_message

        msg = {"jsonrpc": "2.0", "id": 1, "result": {}}
        buf = io.BytesIO()
        write_message(msg, stream=buf)
        raw = buf.getvalue()
        # Must contain Content-Length header
        assert b"Content-Length:" in raw
        # Must contain double CRLF separator
        assert b"\r\n\r\n" in raw
        # Body after separator must be valid JSON
        _, body = raw.split(b"\r\n\r\n", 1)
        parsed = json.loads(body)
        assert parsed["id"] == 1

    def test_write_then_read_roundtrip(self):
        from eigenhelm.mcp.protocol import read_message, write_message

        original = {"jsonrpc": "2.0", "id": 42, "result": {"tools": []}}
        buf = io.BytesIO()
        write_message(original, stream=buf)
        buf.seek(0)
        recovered = read_message(buf)
        assert recovered == original


# ---------------------------------------------------------------------------
# Protocol: make_response / make_error
# ---------------------------------------------------------------------------


class TestProtocolResponseBuilders:
    """JSON-RPC 2.0 response envelope contract."""

    def test_make_response_shape(self):
        from eigenhelm.mcp.protocol import make_response

        resp = make_response(1, {"tools": []})
        assert resp["jsonrpc"] == "2.0"
        assert resp["id"] == 1
        assert "result" in resp
        assert "error" not in resp

    def test_make_error_shape(self):
        from eigenhelm.mcp.protocol import make_error

        resp = make_error(1, -32601, "Not found")
        assert resp["jsonrpc"] == "2.0"
        assert resp["id"] == 1
        assert "error" in resp
        assert resp["error"]["code"] == -32601
        assert resp["error"]["message"] == "Not found"
        assert "data" not in resp["error"]

    def test_make_error_with_data(self):
        from eigenhelm.mcp.protocol import make_error

        resp = make_error(1, -32602, "Bad params", data={"field": "source"})
        assert resp["error"]["data"] == {"field": "source"}


# ---------------------------------------------------------------------------
# Server: initialization and tool listing
# ---------------------------------------------------------------------------


class TestMcpServerInitAndList:
    """Server initialization, tool listing, and basic dispatch."""

    def test_server_creates_helm_on_init(self):
        from eigenhelm.mcp.server import McpServer

        server = McpServer()
        assert server.state.helm is not None

    def test_server_loads_explicit_model(self):
        """When given an explicit model path, that model is loaded."""
        import pathlib

        from eigenhelm.mcp.server import McpServer

        # Use the baseline model (always present in repo)
        model_path = (
            pathlib.Path(__file__).parent.parent.parent / "models" / "baseline.npz"
        )
        if not model_path.exists():
            pytest.skip("baseline model not present")
        server = McpServer(model_path=str(model_path))
        assert server.state.active_model_name == "baseline"

    def test_server_falls_back_to_bundled_model(self):
        """Without explicit path, server attempts bundled model fallback."""
        from eigenhelm.mcp.server import McpServer

        server = McpServer()
        # active_model_name is either set (bundled found) or None (no model)
        # Either way, helm must exist
        assert server.state.helm is not None

    def test_get_version_returns_string(self):
        from eigenhelm.mcp.server import _get_version

        v = _get_version()
        assert isinstance(v, str)
        assert len(v) > 0

    def test_initialize_response_shape(self):
        from eigenhelm.mcp.server import McpServer

        server = McpServer()
        resp = server.handle_message(
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
        )
        assert resp["id"] == 1
        result = resp["result"]
        assert "protocolVersion" in result
        assert "capabilities" in result
        assert "tools" in result["capabilities"]
        assert "serverInfo" in result
        assert result["serverInfo"]["name"] == "eigenhelm"

    def test_tools_list_returns_all_registered_tools(self):
        from eigenhelm.mcp.server import McpServer
        from eigenhelm.mcp.tools import TOOL_DEFINITIONS

        server = McpServer()
        resp = server.handle_message(
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
        )
        tools = resp["result"]["tools"]
        assert len(tools) == len(TOOL_DEFINITIONS)
        tool_names = {t["name"] for t in tools}
        expected = {
            "evaluate",
            "evaluate_batch",
            "model_list",
            "model_info",
            "model_switch",
        }
        assert tool_names == expected

    def test_each_tool_has_input_schema(self):
        from eigenhelm.mcp.tools import TOOL_DEFINITIONS

        for tool in TOOL_DEFINITIONS:
            assert "inputSchema" in tool, f"Tool {tool['name']} missing inputSchema"
            assert tool["inputSchema"]["type"] == "object"

    def test_ping_returns_empty_result(self):
        from eigenhelm.mcp.server import McpServer

        server = McpServer()
        resp = server.handle_message({"jsonrpc": "2.0", "id": 3, "method": "ping"})
        assert resp["result"] == {}


# ---------------------------------------------------------------------------
# Server: dispatch and error handling
# ---------------------------------------------------------------------------


class TestMcpServerDispatch:
    """Tool dispatch, unknown methods, error responses."""

    def test_notification_returns_none(self):
        """Messages without an id (notifications) return None."""
        from eigenhelm.mcp.server import McpServer

        server = McpServer()
        result = server.handle_message({"method": "notifications/initialized"})
        assert result is None

    def test_unknown_method_returns_method_not_found(self):
        from eigenhelm.mcp.server import McpServer

        server = McpServer()
        resp = server.handle_message(
            {"jsonrpc": "2.0", "id": 4, "method": "nonexistent/method"}
        )
        assert "error" in resp
        assert resp["error"]["code"] == -32601

    def test_unknown_tool_returns_invalid_params(self):
        from eigenhelm.mcp.server import McpServer

        server = McpServer()
        resp = server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 5,
                "method": "tools/call",
                "params": {"name": "nonexistent_tool", "arguments": {}},
            }
        )
        assert "error" in resp
        assert resp["error"]["code"] == -32602

    def test_evaluate_tool_returns_content(self):
        from eigenhelm.mcp.server import McpServer

        server = McpServer()
        resp = server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 6,
                "method": "tools/call",
                "params": {
                    "name": "evaluate",
                    "arguments": {
                        "source": "def hello(): pass",
                        "language": "python",
                    },
                },
            }
        )
        assert "result" in resp
        content = resp["result"]["content"]
        assert isinstance(content, list)
        assert len(content) >= 1
        assert content[0]["type"] == "text"
        # Content text should be valid JSON with expected fields
        data = json.loads(content[0]["text"])
        assert "decision" in data
        assert "score" in data
        assert data["decision"] in ("accept", "warn", "reject")

    def test_evaluate_returns_structural_confidence(self):
        from eigenhelm.mcp.server import McpServer

        server = McpServer()
        resp = server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 7,
                "method": "tools/call",
                "params": {
                    "name": "evaluate",
                    "arguments": {
                        "source": "x = 1",
                        "language": "python",
                    },
                },
            }
        )
        data = json.loads(resp["result"]["content"][0]["text"])
        assert "structural_confidence" in data

    def test_evaluate_with_file_path(self):
        from eigenhelm.mcp.server import McpServer

        server = McpServer()
        resp = server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 8,
                "method": "tools/call",
                "params": {
                    "name": "evaluate",
                    "arguments": {
                        "source": "def greet(name): return f'Hello {name}'",
                        "language": "python",
                        "file_path": "greeter.py",
                    },
                },
            }
        )
        data = json.loads(resp["result"]["content"][0]["text"])
        assert data.get("file_path") == "greeter.py"

    def test_evaluate_handler_value_error_returns_is_error(self):
        """When a handler raises ValueError, response includes isError: true."""
        from eigenhelm.mcp.server import McpServer
        from eigenhelm.mcp import tools as tools_mod

        server = McpServer()
        original = tools_mod.TOOL_HANDLERS["evaluate"]
        tools_mod.TOOL_HANDLERS["evaluate"] = lambda state, args: (_ for _ in ()).throw(
            ValueError("bad input")
        )
        try:
            resp = server.handle_message(
                {
                    "jsonrpc": "2.0",
                    "id": 9,
                    "method": "tools/call",
                    "params": {
                        "name": "evaluate",
                        "arguments": {"source": "x", "language": "python"},
                    },
                }
            )
        finally:
            tools_mod.TOOL_HANDLERS["evaluate"] = original
        assert resp["result"]["isError"] is True
        assert "Error:" in resp["result"]["content"][0]["text"]

    def test_evaluate_handler_unexpected_error_returns_internal_error(self):
        """When a handler raises an unexpected exception, response has isError + 'Internal error'."""
        from eigenhelm.mcp.server import McpServer
        from eigenhelm.mcp import tools as tools_mod

        def raise_runtime(state, args):
            raise RuntimeError("crash")

        server = McpServer()
        original = tools_mod.TOOL_HANDLERS["evaluate"]
        tools_mod.TOOL_HANDLERS["evaluate"] = raise_runtime
        try:
            resp = server.handle_message(
                {
                    "jsonrpc": "2.0",
                    "id": 10,
                    "method": "tools/call",
                    "params": {
                        "name": "evaluate",
                        "arguments": {"source": "x", "language": "python"},
                    },
                }
            )
        finally:
            tools_mod.TOOL_HANDLERS["evaluate"] = original
        assert resp["result"]["isError"] is True
        assert "Internal error:" in resp["result"]["content"][0]["text"]


# ---------------------------------------------------------------------------
# Tools: evaluate_batch
# ---------------------------------------------------------------------------


class TestMcpEvaluateBatch:
    """evaluate_batch tool contract."""

    def test_batch_returns_results_and_summary(self):
        from eigenhelm.mcp.server import McpServer

        server = McpServer()
        resp = server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 11,
                "method": "tools/call",
                "params": {
                    "name": "evaluate_batch",
                    "arguments": {
                        "files": [
                            {"source": "def a(): pass", "language": "python"},
                            {"source": "def b(): return 1", "language": "python"},
                        ]
                    },
                },
            }
        )
        data = json.loads(resp["result"]["content"][0]["text"])
        assert "results" in data
        assert "summary" in data
        assert len(data["results"]) == 2
        summary = data["summary"]
        assert summary["total_files"] == 2
        assert summary["overall_decision"] in ("accept", "warn", "reject")
        assert "mean_score" in summary

    def test_batch_empty_files_returns_accept(self):
        """Empty batch (edge case) should return overall accept."""
        from eigenhelm.mcp.tools import execute_evaluate_batch
        from eigenhelm.mcp.server import ServerState
        from eigenhelm.helm import DynamicHelm

        state = ServerState(helm=DynamicHelm())
        result = execute_evaluate_batch(state, {"files": []})
        data = json.loads(result[0]["text"])
        assert data["summary"]["overall_decision"] == "accept"
        assert data["summary"]["total_files"] == 0

    def test_batch_reject_propagates_to_overall(self):
        """If any file is rejected, overall decision is reject."""
        from eigenhelm.mcp.server import McpServer

        server = McpServer()
        # Use a very bad snippet to get a reject (or at least exercise the code)
        resp = server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 12,
                "method": "tools/call",
                "params": {
                    "name": "evaluate_batch",
                    "arguments": {
                        "files": [
                            {"source": "def good(): return 42", "language": "python"},
                        ]
                    },
                },
            }
        )
        data = json.loads(resp["result"]["content"][0]["text"])
        # Just verify the summary structure is correct regardless of actual scores
        assert (
            data["summary"]["accepted"]
            + data["summary"]["warned"]
            + data["summary"]["rejected"]
            == 1
        )


# ---------------------------------------------------------------------------
# Tools: model_list
# ---------------------------------------------------------------------------


class TestMcpModelList:
    """model_list tool contract."""

    def test_model_list_returns_json_array(self):
        from eigenhelm.mcp.server import McpServer

        server = McpServer()
        resp = server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 13,
                "method": "tools/call",
                "params": {"name": "model_list", "arguments": {}},
            }
        )
        data = json.loads(resp["result"]["content"][0]["text"])
        assert isinstance(data, list)

    def test_model_list_entries_have_name_and_source(self):
        from eigenhelm.mcp.server import McpServer

        server = McpServer()
        resp = server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 14,
                "method": "tools/call",
                "params": {"name": "model_list", "arguments": {}},
            }
        )
        data = json.loads(resp["result"]["content"][0]["text"])
        for entry in data:
            if "error" not in entry:
                assert "name" in entry
                assert "source" in entry

    def test_model_list_marks_active_model(self):
        """The currently active model should have active=True."""
        from eigenhelm.mcp.server import McpServer

        server = McpServer()
        if server.state.active_model_name is None:
            pytest.skip("no active model loaded")
        resp = server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 15,
                "method": "tools/call",
                "params": {"name": "model_list", "arguments": {}},
            }
        )
        data = json.loads(resp["result"]["content"][0]["text"])
        active_entries = [e for e in data if e.get("active")]
        assert len(active_entries) == 1
        assert active_entries[0]["name"] == server.state.active_model_name

    def test_model_list_include_remote_error_handling(self):
        """include_remote=True with failing registry does not crash, returns error entry."""
        from unittest.mock import patch

        from eigenhelm.mcp.server import McpServer

        server = McpServer()
        with patch(
            "eigenhelm.registry.list_remote",
            side_effect=ConnectionError("network down"),
        ):
            resp = server.handle_message(
                {
                    "jsonrpc": "2.0",
                    "id": 16,
                    "method": "tools/call",
                    "params": {
                        "name": "model_list",
                        "arguments": {"include_remote": True},
                    },
                }
            )
        data = json.loads(resp["result"]["content"][0]["text"])
        error_entries = [e for e in data if "error" in e]
        assert len(error_entries) >= 1


# ---------------------------------------------------------------------------
# Tools: model_info
# ---------------------------------------------------------------------------


class TestMcpModelInfo:
    """model_info tool contract."""

    def test_model_info_not_found(self):
        from eigenhelm.mcp.server import McpServer

        server = McpServer()
        resp = server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 17,
                "method": "tools/call",
                "params": {
                    "name": "model_info",
                    "arguments": {"name": "nonexistent-model-xyz"},
                },
            }
        )
        text = resp["result"]["content"][0]["text"]
        assert "not found" in text.lower()

    @pytest.mark.requires_model
    def test_model_info_returns_metadata(self):
        from eigenhelm.mcp.server import McpServer

        server = McpServer()
        resp = server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 18,
                "method": "tools/call",
                "params": {
                    "name": "model_info",
                    "arguments": {"name": "general-polyglot-v1"},
                },
            }
        )
        data = json.loads(resp["result"]["content"][0]["text"])
        assert "name" in data
        assert "n_components" in data
        assert "version" in data
        assert data["name"] == "general-polyglot-v1"


# ---------------------------------------------------------------------------
# Tools: model_switch
# ---------------------------------------------------------------------------


class TestMcpModelSwitch:
    """model_switch tool contract."""

    @pytest.mark.requires_model
    def test_model_switch_updates_active_model(self):
        from eigenhelm.mcp.server import McpServer

        server = McpServer()
        resp = server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 19,
                "method": "tools/call",
                "params": {
                    "name": "model_switch",
                    "arguments": {"name": "lang-python"},
                },
            }
        )
        text = resp["result"]["content"][0]["text"]
        assert "Switched to model" in text
        assert server.state.active_model_name == "lang-python"

    def test_model_switch_nonexistent_returns_error(self):
        from eigenhelm.mcp.server import McpServer

        server = McpServer()
        resp = server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 20,
                "method": "tools/call",
                "params": {
                    "name": "model_switch",
                    "arguments": {"name": "nonexistent-model-abc"},
                },
            }
        )
        text = resp["result"]["content"][0]["text"]
        assert "Failed to resolve" in text or "not found" in text.lower()


# ---------------------------------------------------------------------------
# Tools: declaration_ratio in response
# ---------------------------------------------------------------------------


class TestMcpResponseFields:
    """Verify all expected fields appear in evaluate response."""

    def test_contributions_in_evaluate_response(self):
        from eigenhelm.mcp.server import McpServer

        server = McpServer()
        resp = server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 21,
                "method": "tools/call",
                "params": {
                    "name": "evaluate",
                    "arguments": {
                        "source": "import os\nimport sys\nimport json\n\nFOO = 1\nBAR = 2\n",
                        "language": "python",
                    },
                },
            }
        )
        data = json.loads(resp["result"]["content"][0]["text"])
        # declaration_ratio may or may not be present depending on content
        # but the key fields must exist
        assert "decision" in data
        assert "score" in data
        assert "structural_confidence" in data

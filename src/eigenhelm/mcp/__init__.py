"""MCP (Model Context Protocol) server for eigenhelm.

Exposes eigenhelm evaluation and model management as MCP tools over stdio,
using a hand-rolled JSON-RPC 2.0 handler (zero external dependencies).

Public API:
    run_server() — blocking stdio event loop
    McpServer    — server with tool dispatch
"""

from eigenhelm.mcp.server import McpServer, run_server

__all__ = ["McpServer", "run_server"]

"""eigenhelm-mcp CLI — start the MCP stdio server."""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    """Entry point for eigenhelm-mcp."""
    parser = argparse.ArgumentParser(
        prog="eigenhelm-mcp",
        description="Start the eigenhelm MCP server (stdio transport).",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Path to .npz eigenspace model (default: project config or bundled model).",
    )
    args = parser.parse_args(argv)

    try:
        from eigenhelm.mcp import run_server

        run_server(model_path=args.model)
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        print(f"eigenhelm-mcp ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

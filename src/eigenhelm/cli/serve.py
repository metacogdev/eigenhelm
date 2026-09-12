"""eigenhelm-serve CLI — start the FastAPI sidecar server.

Usage:
    eigenhelm-serve --host 0.0.0.0 --port 8080 --model model.npz
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


def main(argv: list[str] | None = None) -> None:
    """Entry point for eigenhelm-serve."""
    try:
        import uvicorn  # noqa: F401, I001
        from eigenhelm.serve import create_app  # noqa: I001
    except ImportError:
        print(
            "ERROR: eigenhelm[serve] extras not installed. Run: pip install 'eigenhelm[serve]'",
            file=sys.stderr,
        )
        sys.exit(1)

    parser = argparse.ArgumentParser(
        prog="eigenhelm-serve",
        description="Start the eigenhelm evaluation sidecar server",
    )
    parser.add_argument(
        "--host", default="0.0.0.0", help="Bind address (default: 0.0.0.0)"
    )
    parser.add_argument("--port", type=int, default=8080, help="Port (default: 8080)")
    from eigenhelm.config import find_config, load_config
    from eigenhelm.cli._common import add_model_argument

    add_model_argument(parser)
    parser.add_argument(
        "--timeout-graceful-shutdown",
        type=int,
        default=30,
        help="Seconds to wait for in-flight requests on SIGTERM (default: 30)",
    )
    parser.add_argument(
        "--max-body-bytes",
        type=int,
        default=None,
        help="Max request body size in bytes.",
    )
    parser.add_argument(
        "--max-batch-bytes",
        type=int,
        default=None,
        help="Max batch size in bytes.",
    )
    parser.add_argument(
        "--request-timeout",
        type=float,
        default=None,
        help="Request timeout in seconds.",
    )
    args = parser.parse_args(argv)

    try:
        from eigenhelm.config import find_config, load_config
        from eigenhelm.cli._common import resolve_and_load_model

        config_path = find_config(Path.cwd())
        config = load_config(config_path) if config_path else None
        eigenspace, path = resolve_and_load_model(args.model, config)

        print(
            f"INFO: Loading eigenspace model "
            f"(version={eigenspace.version}, corpus_hash={eigenspace.corpus_hash})",
            file=sys.stderr,
        )
    except Exception as exc:
        print(f"ERROR: Failed to load model: {exc}", file=sys.stderr)
        sys.exit(1)

    # Resolve limits (CLI > config > default)
    from eigenhelm.serve import DEFAULT_MAX_BODY_BYTES

    max_body_bytes = args.max_body_bytes or (
        config.serve.max_body_bytes
        if config and config.serve.max_body_bytes
        else DEFAULT_MAX_BODY_BYTES
    )
    max_batch_bytes = args.max_batch_bytes or (
        config.serve.max_batch_bytes
        if config and config.serve.max_batch_bytes
        else 10_485_760
    )
    timeout_seconds = args.request_timeout or (
        config.serve.timeout_seconds
        if config and config.serve.timeout_seconds
        else 30.0
    )

    app = create_app(
        eigenspace=eigenspace,
        max_body_bytes=max_body_bytes,
        max_batch_bytes=max_batch_bytes,
        timeout_seconds=timeout_seconds,
    )
    model_status = "loaded" if eigenspace else "none"
    print(
        f"INFO: eigenhelm-serve starting on {args.host}:{args.port} (model={model_status})",
        file=sys.stderr,
    )

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        timeout_graceful_shutdown=args.timeout_graceful_shutdown,
    )


if __name__ == "__main__":
    main()

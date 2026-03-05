"""eigenhelm-serve CLI — start the FastAPI sidecar server.

Usage:
    eigenhelm-serve --host 0.0.0.0 --port 8080 --model model.npz
"""

from __future__ import annotations

import argparse
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
    parser.add_argument("--host", default="0.0.0.0", help="Bind address (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8080, help="Port (default: 8080)")
    parser.add_argument("--model", default=None, help="Path to .npz eigenspace model")
    parser.add_argument(
        "--timeout-graceful-shutdown",
        type=int,
        default=30,
        help="Seconds to wait for in-flight requests on SIGTERM (default: 30)",
    )
    args = parser.parse_args(argv)

    eigenspace = None
    if args.model:
        try:
            from eigenhelm.eigenspace import load_model

            eigenspace = load_model(args.model)
            print(
                f"INFO: Loading eigenspace model from {args.model} "
                f"(version={eigenspace.version}, corpus_hash={eigenspace.corpus_hash})",
                file=sys.stderr,
            )
        except (FileNotFoundError, OSError) as exc:
            print(f"ERROR: Failed to load model: {exc}", file=sys.stderr)
            sys.exit(1)
    else:
        print(
            "WARNING: No eigenspace model loaded; running in low-confidence mode",
            file=sys.stderr,
        )

    app = create_app(eigenspace=eigenspace)
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

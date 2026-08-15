"""eigenhelm-harness CLI — compare two corpora with Mann-Whitney U test.

Usage:
    eigenhelm-harness --before corpus/before/ --after corpus/after/
    eigenhelm-harness --before before/ --after after/ --model model.npz --json

Exit codes:
    0  Harness completed (regardless of significance)
    1  One or both corpus directories empty/unreadable
    2  Runtime error
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from eigenhelm.harness.report import format_harness_human, format_harness_json


def main(argv: list[str] | None = None) -> int:
    """Entry point for eigenhelm-harness.

    Returns exit code: 0 (success), 1 (empty corpus), 2 (runtime error).
    """
    parser = argparse.ArgumentParser(
        prog="eigenhelm-harness",
        description="Compare two corpora with statistical testing",
    )
    parser.add_argument(
        "--before", required=True, type=Path, help="Before corpus directory"
    )
    parser.add_argument(
        "--after", required=True, type=Path, help="After corpus directory"
    )
    parser.add_argument("--model", default=None, help="Path to .npz eigenspace model")
    parser.add_argument(
        "--json", dest="json_output", action="store_true", help="JSON output"
    )
    args = parser.parse_args(argv)

    try:
        eigenspace = None
        if args.model:
            from eigenhelm.eigenspace import load_model

            eigenspace = load_model(args.model)

        from eigenhelm.harness.runner import run_harness

        report = run_harness(args.before, args.after, eigenspace=eigenspace)

        if args.json_output:
            print(format_harness_json(report))
        else:
            print(format_harness_human(report))

        return 0

    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

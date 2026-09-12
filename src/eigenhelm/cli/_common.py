from __future__ import annotations

import argparse
import sys

from eigenhelm.eigenspace import load_model, EigenspaceModel
from eigenhelm.config import ProjectConfig
from eigenhelm.trained_models import default_model_path as get_bundled_model_path


def add_model_argument(parser: argparse.ArgumentParser) -> None:
    """Add the standard --model argument to an argparse.ArgumentParser."""
    parser.add_argument(
        "--model",
        default=None,
        help="Path to .npz eigenspace model (overrides config and bundled default).",
    )


def resolve_model_path(
    cli_model: str | None, config: ProjectConfig | None = None
) -> str:
    """
    Resolve model path in priority order:
    1. CLI arg
    2. Config file
    3. Bundled default
    """
    if cli_model is not None:
        return cli_model
    if config is not None and config.model:
        return str(config.model)
    return str(get_bundled_model_path())


def resolve_and_load_model(
    cli_model: str | None, config: ProjectConfig | None = None
) -> tuple[EigenspaceModel, str]:
    """
    Resolve model path and load the model.
    Returns the EigenspaceModel and the path it was loaded from.
    """
    path = resolve_model_path(cli_model, config)
    try:
        model = load_model(path)
        return model, path
    except Exception as exc:
        print(f"ERROR: Failed to load model from {path}: {exc}", file=sys.stderr)
        sys.exit(1)


def add_strict_lenient_args(parser: argparse.ArgumentParser) -> None:
    """Add mutually-exclusive --strict/--lenient group to an argparse.ArgumentParser."""
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="Treat warn decisions as reject (exit code 2 / block commit).",
    )
    group.add_argument(
        "--lenient",
        action="store_true",
        default=False,
        help="Treat warn decisions as accept (exit code 0 / override config).",
    )

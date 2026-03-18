"""Bundled trained models for eigenhelm.

Models are shipped with the package so eigenhelm works out of the box
without a separate training step.
"""

from __future__ import annotations

from importlib import resources
from pathlib import Path

DEFAULT_MODEL = "general-polyglot-v1.npz"


def default_model_path() -> Path:
    """Return the path to the bundled default model.

    The default model is the Class C polyglot model trained on
    Python, JavaScript, TypeScript, Go, and Rust corpora.
    """
    return _model_path(DEFAULT_MODEL)


def _model_path(name: str) -> Path:
    """Return the path to a bundled model by filename."""
    ref = resources.files(__package__) / name
    # resources.files returns a Traversable; resolve to a real path
    return Path(str(ref))

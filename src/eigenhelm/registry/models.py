"""Data models for the model registry."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelEntry:
    """A model listed in the registry manifest."""

    name: str
    description: str
    language: str  # "polyglot" or specific language
    corpus_class: str  # "A", "B", "C"
    n_components: int
    n_training_files: int
    download_url: str
    sha256: str
    size_bytes: int
    version: str


@dataclass(frozen=True)
class LocalModel:
    """A model available on the local filesystem."""

    name: str
    path: str
    bundled: bool  # True if shipped with the package

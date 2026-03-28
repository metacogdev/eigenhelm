"""Config file loader for eigenhelm.

Provides:
  - load_config(path): parse .eigenhelm.toml -> ProjectConfig
  - find_config(start): walk up directory tree to find .eigenhelm.toml
"""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path

from eigenhelm.config.models import PathRule, ProjectConfig, ThresholdConfig

_KNOWN_TOP_LEVEL_KEYS = frozenset(
    {"model", "language", "strict", "thresholds", "paths", "language_overrides"}
)


def _parse_thresholds(data: dict) -> ThresholdConfig:
    return ThresholdConfig(
        accept=float(data["accept"]) if "accept" in data else None,
        reject=float(data["reject"]) if "reject" in data else None,
    )


def _parse_path_rule(data: dict) -> PathRule:
    glob = data.get("glob", "")
    thresholds_data = data.get("thresholds", {})
    thresholds = (
        _parse_thresholds(thresholds_data) if thresholds_data else ThresholdConfig()
    )
    return PathRule(glob=glob, thresholds=thresholds)


def load_config(path: Path) -> ProjectConfig:
    """Parse .eigenhelm.toml at the given path and return a ProjectConfig.

    Raises:
        FileNotFoundError: if the file does not exist.
        ValueError: if the TOML contains invalid values.
        tomllib.TOMLDecodeError: if the TOML is malformed.
    """
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open("rb") as f:
        data = tomllib.load(f)

    # Warn about unknown top-level keys (FR-015)
    for key in data:
        if key not in _KNOWN_TOP_LEVEL_KEYS:
            print(
                f"WARNING: Unknown config key {key!r} in {path} (ignored)",
                file=sys.stderr,
            )

    # Parse thresholds
    thresholds_data = data.get("thresholds", {})
    try:
        thresholds = _parse_thresholds(thresholds_data)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"Invalid [thresholds] in {path}: {exc}") from exc

    # Parse path rules
    paths_data = data.get("paths", [])
    try:
        paths = tuple(_parse_path_rule(p) for p in paths_data)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"Invalid [[paths]] entry in {path}: {exc}") from exc

    # Parse language_overrides
    language_overrides = dict(data.get("language_overrides", {}))
    for ext in language_overrides:
        if not ext.startswith("."):
            raise ValueError(
                f"language_overrides key must start with '.', got {ext!r} in {path}"
            )

    try:
        return ProjectConfig(
            model=data.get("model"),
            language=data.get("language"),
            strict=bool(data.get("strict", False)),
            thresholds=thresholds,
            paths=paths,
            language_overrides=language_overrides,
        )
    except (ValueError, TypeError) as exc:
        raise ValueError(f"Invalid config in {path}: {exc}") from exc


def find_config(start: Path) -> Path | None:
    """Walk up the directory tree from start looking for .eigenhelm.toml.

    Returns the first found path, or None if not found.
    """
    current = start.resolve()
    # Walk up to filesystem root
    while True:
        candidate = current / ".eigenhelm.toml"
        if candidate.is_file():
            return candidate
        parent = current.parent
        if parent == current:
            # Reached filesystem root
            return None
        current = parent

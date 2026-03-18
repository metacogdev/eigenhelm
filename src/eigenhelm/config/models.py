"""Config data model for eigenhelm project configuration.

These frozen dataclasses represent the parsed contents of a `.eigenhelm.toml` file.
"""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ThresholdConfig:
    """Accept/reject score thresholds.

    Invariant: accept < reject, both in [0.0, 1.0].
    Scores <= accept are accepted.
    Scores >= reject are rejected.
    Scores in between are warned.

    When accept or reject is None, the value was not explicitly configured
    and should fall through to model calibration or hardcoded defaults.
    """

    accept: float | None = None
    reject: float | None = None

    def __post_init__(self) -> None:
        if self.accept is not None and not (0.0 <= self.accept <= 1.0):
            raise ValueError(f"accept must be in [0.0, 1.0], got {self.accept}")
        if self.reject is not None and not (0.0 <= self.reject <= 1.0):
            raise ValueError(f"reject must be in [0.0, 1.0], got {self.reject}")
        if (
            self.accept is not None
            and self.reject is not None
            and self.accept >= self.reject
        ):
            raise ValueError(
                f"accept must be < reject, got accept={self.accept}, reject={self.reject}"
            )


@dataclass(frozen=True)
class PathRule:
    """Per-glob threshold override.

    glob: non-empty glob pattern (e.g., 'src/core/**').
    thresholds: ThresholdConfig overriding global thresholds for matching files.
    """

    glob: str
    thresholds: ThresholdConfig = field(default_factory=ThresholdConfig)

    def __post_init__(self) -> None:
        if not self.glob:
            raise ValueError("PathRule.glob must be a non-empty string")

    def matches(self, file_path: str) -> bool:
        """Return True if file_path matches this rule's glob pattern."""
        return fnmatch.fnmatch(file_path, self.glob)


@dataclass(frozen=True)
class ProjectConfig:
    """Complete parsed .eigenhelm.toml.

    model: path or name of .npz eigenspace model file.
    language: default language override for all files.
    strict: if True, treat warn decisions as reject.
    thresholds: global accept/reject thresholds.
    paths: ordered tuple of path rules; last-match-wins semantics.
    language_overrides: mapping of file extension -> language key (keys must start with '.').
    """

    model: str | None = None
    language: str | None = None
    strict: bool = False
    thresholds: ThresholdConfig = field(default_factory=ThresholdConfig)
    paths: tuple[PathRule, ...] = ()
    language_overrides: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for ext in self.language_overrides:
            if not ext.startswith("."):
                raise ValueError(
                    f"language_overrides key must start with '.', got {ext!r}"
                )

    def thresholds_for(self, file_path: str) -> ThresholdConfig:
        """Return the most specific ThresholdConfig for a file path.

        Iterates path rules in order; last matching rule wins.
        Falls back to global thresholds if no rule matches.
        """
        result = self.thresholds
        for rule in self.paths:
            if rule.matches(file_path):
                result = rule.thresholds
        return result

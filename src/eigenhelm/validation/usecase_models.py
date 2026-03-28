"""Data models for real-world use case benchmarking.

All value objects are frozen dataclasses following the project convention.
"""

from __future__ import annotations

import enum
import json
from dataclasses import dataclass, field
from pathlib import Path


class FileCategory(enum.Enum):
    """Classification of a source file for benchmark stratification."""

    IMPLEMENTATION = "implementation"
    TEST = "test"
    SCHEMA = "schema"
    INIT = "init"
    GENERATED = "generated"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class FileEvaluation:
    """A single file's evaluation result with category metadata."""

    file_path: str
    project: str
    category: FileCategory
    score: float
    decision: str
    percentile: float | None = None
    dim_scores: dict[str, float] = field(default_factory=dict)
    n_directives: int = 0
    directive_categories: tuple[str, ...] = ()


@dataclass(frozen=True)
class CategoryDistribution:
    """Score distribution statistics for one file category."""

    category: FileCategory
    n_files: int
    min: float
    p10: float
    p25: float
    median: float
    p75: float
    p90: float
    max: float


@dataclass(frozen=True)
class DimensionDiscrimination:
    """Per-dimension discrimination metrics for a file category."""

    dimension: str
    category: FileCategory
    cohens_d: float | None
    cv: float
    mean: float
    std: float
    signal_quality: str  # "strong", "medium", "weak", "noise"


@dataclass(frozen=True)
class QualityTarget:
    """A tracked metric with baseline and target values."""

    name: str
    description: str
    baseline: float | None
    target: float
    direction: str  # "lower_is_better" or "higher_is_better"

    @property
    def met(self) -> bool:
        if self.baseline is None:
            return False
        if self.direction == "lower_is_better":
            return self.baseline <= self.target
        return self.baseline >= self.target


@dataclass(frozen=True)
class RegressionAlert:
    """Alert when a quality target regresses between benchmark runs."""

    target_name: str
    previous_value: float | None
    current_value: float | None
    target_value: float
    was_met: bool
    now_met: bool
    message: str


@dataclass(frozen=True)
class CommitReplayResult:
    """Result of evaluating changed files in a single commit."""

    commit_sha: str
    n_files_changed: int
    n_flagged: int
    n_false_positive: int  # flagged non-implementation files
    all_noise: bool  # True when every flag is a FP
    file_results: tuple[FileEvaluation, ...] = ()


@dataclass(frozen=True)
class BenchmarkReport:
    """Top-level container for a benchmark run."""

    version: str = "1.0"
    date: str = ""
    model: str = ""
    model_version: str = ""
    git_sha: str | None = None
    corpus_version: str = ""
    n_files: int = 0
    n_projects: int = 0
    categories: tuple[CategoryDistribution, ...] = ()
    dimension_discrimination: tuple[DimensionDiscrimination, ...] = ()
    fp_rate: float | None = None
    fn_rate: float | None = None
    attribution_precision: float | None = None
    targets: tuple[QualityTarget, ...] = ()
    file_evaluations: tuple[FileEvaluation, ...] = ()

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dict."""
        return {
            "version": self.version,
            "date": self.date,
            "model": self.model,
            "model_version": self.model_version,
            "git_sha": self.git_sha,
            "corpus_version": self.corpus_version,
            "n_files": self.n_files,
            "n_projects": self.n_projects,
            "categories": [
                {
                    "category": c.category.value,
                    "n_files": c.n_files,
                    "min": c.min,
                    "p10": c.p10,
                    "p25": c.p25,
                    "median": c.median,
                    "p75": c.p75,
                    "p90": c.p90,
                    "max": c.max,
                }
                for c in self.categories
            ],
            "dimension_discrimination": [
                {
                    "dimension": d.dimension,
                    "category": d.category.value,
                    "cohens_d": d.cohens_d,
                    "cv": d.cv,
                    "mean": d.mean,
                    "std": d.std,
                    "signal_quality": d.signal_quality,
                }
                for d in self.dimension_discrimination
            ],
            "fp_rate": self.fp_rate,
            "fn_rate": self.fn_rate,
            "attribution_precision": self.attribution_precision,
            "targets": [
                {
                    "name": t.name,
                    "description": t.description,
                    "baseline": t.baseline,
                    "target": t.target,
                    "direction": t.direction,
                    "met": t.met,
                }
                for t in self.targets
            ],
        }

    def to_json(self) -> str:
        """Serialize to a JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    def save(self, path: Path) -> None:
        """Write JSON report to file."""
        path.write_text(self.to_json())

    def render(self) -> str:
        """Render a human-readable summary."""
        lines = [
            f"Use Case Benchmark Report ({self.date})",
            f"Model: {self.model} ({self.model_version})",
            f"Files: {self.n_files} across {self.n_projects} projects",
            "",
            "Per-Category Score Distributions:",
            f"  {'Category':<20s} {'N':>5s} {'Min':>6s} {'P25':>6s} {'Med':>6s} {'P75':>6s} {'Max':>6s}",
        ]
        for c in self.categories:
            lines.append(
                f"  {c.category.value:<20s} {c.n_files:>5d} {c.min:>6.2f} "
                f"{c.p25:>6.2f} {c.median:>6.2f} {c.p75:>6.2f} {c.max:>6.2f}"
            )

        if self.dimension_discrimination:
            # Group by category, show implementation first
            impl_dims = [
                d
                for d in self.dimension_discrimination
                if d.category == FileCategory.IMPLEMENTATION
            ]
            if impl_dims:
                lines.append("")
                lines.append("Dimension Discrimination (implementation files):")
                lines.append(
                    f"  {'Dimension':<25s} {'d':>6s} {'CV':>6s} {'Signal':<8s}"
                )
                for d in impl_dims:
                    d_str = f"{d.cohens_d:.2f}" if d.cohens_d is not None else "  N/A"
                    lines.append(
                        f"  {d.dimension:<25s} {d_str:>6s} {d.cv:>6.2f} {d.signal_quality:<8s}"
                    )

        if self.targets:
            lines.append("")
            lines.append("Quality Targets:")
            for t in self.targets:
                status = "PASS" if t.met else "FAIL"
                baseline_str = f"{t.baseline:.2f}" if t.baseline is not None else "N/A"
                lines.append(
                    f"  [{status}] {t.name}: {baseline_str} (target: {t.target:.2f}, {t.direction})"
                )

        return "\n".join(lines)

"""Human-expert correlation benchmark for eigenhelm scoring validation.

Loads a curated benchmark of functions with human quality ratings,
evaluates each with AestheticCritic, and computes Spearman's rank
correlation between human ratings and eigenhelm scores.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class BenchmarkEntry:
    """A single function with human quality rating."""

    file: str
    function_name: str
    language: str
    human_rating: float  # 1-5 Likert scale
    n_raters: int
    source: str = ""  # Populated after loading


@dataclass
class BenchmarkResult:
    """Aggregate results from benchmark evaluation."""

    spearman_rho: float
    p_value: float
    n_samples: int
    human_ratings: list[float]
    eigenhelm_scores: list[float]
    classifications: list[str]  # accept/marginal/reject per function


class HumanBenchmark:
    """Load and evaluate a human-expert benchmark set.

    Args:
        benchmark_path: Path to benchmark.json fixture.
        samples_dir: Path to directory containing sample .py files.
    """

    def __init__(self, benchmark_path: Path, samples_dir: Path) -> None:
        self.benchmark_path = benchmark_path
        self.samples_dir = samples_dir
        self.entries: list[BenchmarkEntry] = []

    def load(self) -> list[BenchmarkEntry]:
        """Load benchmark entries and their source code."""
        with open(self.benchmark_path) as f:
            data = json.load(f)

        self.entries = []
        for item in data["functions"]:
            entry = BenchmarkEntry(
                file=item["file"],
                function_name=item["function_name"],
                language=item["language"],
                human_rating=float(item["human_rating"]),
                n_raters=int(item["n_raters"]),
            )
            # Load source from file
            source_path = self.samples_dir / item["file"]
            if source_path.exists():
                entry.source = source_path.read_text(encoding="utf-8")
            self.entries.append(entry)

        return self.entries

    def evaluate(
        self,
        eigenspace_model: Any | None = None,
    ) -> BenchmarkResult:
        """Run eigenhelm evaluation on all benchmark entries and compute correlation.

        Args:
            eigenspace_model: Optional EigenspaceModel for high-confidence scoring.

        Returns:
            BenchmarkResult with Spearman's rho and per-function classifications.
        """
        from scipy.stats import spearmanr

        from eigenhelm.critic import AestheticCritic

        if not self.entries:
            self.load()

        critic = AestheticCritic()
        human_ratings: list[float] = []
        eigenhelm_scores: list[float] = []
        classifications: list[str] = []

        for entry in self.entries:
            if not entry.source:
                continue
            critique = critic.evaluate(entry.source, entry.language)
            human_ratings.append(entry.human_rating)
            # Lower loss = better code, so invert for correlation with human ratings
            eigenhelm_scores.append(1.0 - critique.score.value)
            classifications.append(critique.quality_assessment)

        if len(human_ratings) < 2:
            return BenchmarkResult(
                spearman_rho=0.0,
                p_value=1.0,
                n_samples=len(human_ratings),
                human_ratings=human_ratings,
                eigenhelm_scores=eigenhelm_scores,
                classifications=classifications,
            )

        rho, p_value = spearmanr(human_ratings, eigenhelm_scores)

        return BenchmarkResult(
            spearman_rho=float(rho),
            p_value=float(p_value),
            n_samples=len(human_ratings),
            human_ratings=human_ratings,
            eigenhelm_scores=eigenhelm_scores,
            classifications=classifications,
        )

    def report(self, result: BenchmarkResult) -> str:
        """Format benchmark results as human-readable report."""
        lines = [
            "eigenhelm Benchmark Report",
            f"  Samples:          {result.n_samples}",
            f"  Spearman's rho:   {result.spearman_rho:.4f}",
            f"  p-value:          {result.p_value:.4e}",
        ]

        if result.classifications:
            accept = sum(1 for c in result.classifications if c == "accept")
            marginal = sum(1 for c in result.classifications if c == "marginal")
            reject = sum(1 for c in result.classifications if c == "reject")
            lines.append(
                f"  Classifications:  {accept} accept, "
                f"{marginal} marginal, {reject} reject"
            )

            # Check: no reject on human-rated excellent (4-5)
            excellent_rejects = sum(
                1
                for hr, cl in zip(result.human_ratings, result.classifications, strict=False)
                if hr >= 4.0 and cl == "reject"
            )
            if excellent_rejects > 0:
                lines.append(
                    f"  WARNING: {excellent_rejects} excellent"
                    " functions classified as reject"
                )

        return "\n".join(lines)

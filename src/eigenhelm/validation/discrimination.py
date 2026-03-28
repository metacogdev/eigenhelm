"""Cross-language discrimination test infrastructure (009-model-fleet).

Validates whether trained eigenspace models meaningfully separate in-corpus
(elite) code from out-of-corpus (generic) code using Cohen's d effect size.
Lower aesthetic loss = higher quality; positive d = in-corpus scores better.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

from eigenhelm.models import EigenspaceModel


@dataclass(frozen=True)
class DiscriminationReport:
    """Per-language discrimination test result."""

    language: str
    corpus_class: str
    n_components: int
    cumulative_variance: float
    sigma_drift: float
    sigma_virtue: float
    mean_in_score: float
    mean_out_score: float
    effect_size: float  # Cohen's d = (mean_out - mean_in) / pooled_std
    passed: bool  # True if effect_size > 0.5


@dataclass(frozen=True)
class DiscriminationSummary:
    """Aggregated discrimination results across languages."""

    reports: tuple[DiscriminationReport, ...]

    @property
    def all_passed(self) -> bool:
        """True only if every report passed."""
        return all(r.passed for r in self.reports)


def _evaluate_samples(
    model: EigenspaceModel,
    sample_dir: Path,
) -> list[float]:
    """Evaluate code samples in a directory and return aesthetic loss scores.

    Each file is read, parsed for code units, projected into the eigenspace,
    and evaluated using AestheticCritic. Returns per-unit loss values.
    """
    from eigenhelm.critic.aesthetic_critic import AestheticCritic
    from eigenhelm.eigenspace.projection import project
    from eigenhelm.training.corpus import EXTENSION_TO_LANGUAGE
    from eigenhelm.virtue_extractor import VirtueExtractor

    extractor = VirtueExtractor()
    critic = AestheticCritic()
    scores: list[float] = []

    for f in sorted(sample_dir.iterdir()):
        if not f.is_file():
            continue
        if f.suffix not in EXTENSION_TO_LANGUAGE:
            continue

        source = f.read_text(encoding="utf-8", errors="replace")
        language = EXTENSION_TO_LANGUAGE[f.suffix]

        try:
            vectors = extractor.extract(source, language)
        except Exception:
            continue

        for fv in vectors:
            proj = project(fv, model)
            critique = critic.evaluate(source, language, projection=proj)
            scores.append(critique.score.value)

    return scores


def _cohens_d(group_a: list[float], group_b: list[float]) -> float:
    """Compute Cohen's d = (mean_b - mean_a) / pooled_std.

    Positive d means group_b has higher values than group_a.
    For discrimination: group_a = in-corpus (lower loss = better),
    group_b = out-of-corpus (higher loss = worse).
    """
    n_a, n_b = len(group_a), len(group_b)
    if n_a < 2 or n_b < 2:
        return 0.0

    mean_a = sum(group_a) / n_a
    mean_b = sum(group_b) / n_b

    var_a = sum((x - mean_a) ** 2 for x in group_a) / (n_a - 1)
    var_b = sum((x - mean_b) ** 2 for x in group_b) / (n_b - 1)

    pooled_var = ((n_a - 1) * var_a + (n_b - 1) * var_b) / (n_a + n_b - 2)
    pooled_std = math.sqrt(pooled_var)

    if pooled_std == 0:
        return 0.0

    return (mean_b - mean_a) / pooled_std


def run_discrimination_test(
    model: EigenspaceModel,
    in_corpus_dir: Path,
    out_of_corpus_dir: Path,
    *,
    cumulative_variance: float = 0.0,
) -> DiscriminationReport:
    """Run a discrimination test for a single model.

    Args:
        model: Trained eigenspace model to evaluate against.
        in_corpus_dir: Directory of in-corpus code samples.
        out_of_corpus_dir: Directory of out-of-corpus code samples.

    Returns:
        DiscriminationReport with effect size and pass/fail status.
    """
    import numpy as np

    in_scores = _evaluate_samples(model, in_corpus_dir)
    out_scores = _evaluate_samples(model, out_of_corpus_dir)

    mean_in = float(np.mean(in_scores)) if in_scores else float("nan")
    mean_out = float(np.mean(out_scores)) if out_scores else float("nan")
    effect_size = _cohens_d(in_scores, out_scores)

    # cumulative_variance is passed by caller (from inspect_model or .npz)

    return DiscriminationReport(
        language=model.language or "unknown",
        corpus_class=model.corpus_class or "unknown",
        n_components=model.n_components,
        cumulative_variance=cumulative_variance,
        sigma_drift=model.sigma_drift,
        sigma_virtue=model.sigma_virtue,
        mean_in_score=mean_in,
        mean_out_score=mean_out,
        effect_size=effect_size,
        passed=effect_size > 0.5,
    )


def build_summary(reports: list[DiscriminationReport]) -> DiscriminationSummary:
    """Build a summary from per-language reports."""
    return DiscriminationSummary(reports=tuple(reports))


def render_human(summary: DiscriminationSummary) -> str:
    """Render a human-readable discrimination report table."""
    header = (
        f"{'Language':<12} {'Components':>10} {'Variance':>8} "
        f"{'σ_drift':>8} {'σ_virtue':>8} "
        f"{'In-Score':>9} {'Out-Score':>10} {'Effect Size':>11} {'Pass':>5}"
    )
    sep = "-" * len(header)

    rows: list[str] = []
    for r in summary.reports:
        status = "PASS" if r.passed else "FAIL"
        rows.append(
            f"{r.language:<12} {r.n_components:>10} {r.cumulative_variance:>8.2f} "
            f"{r.sigma_drift:>8.4f} {r.sigma_virtue:>8.4f} "
            f"{r.mean_in_score:>9.4f} {r.mean_out_score:>10.4f} {r.effect_size:>11.4f} {status:>5}"
        )

    overall = "ALL PASSED" if summary.all_passed else "SOME FAILED"
    return "\n".join(
        [
            "Cross-Language Discrimination Report",
            sep,
            header,
            sep,
            *rows,
            sep,
            f"Overall: {overall}",
        ]
    )


def render_json(summary: DiscriminationSummary) -> str:
    """Render a machine-parseable JSON discrimination report."""
    data = {
        "reports": [
            {
                "language": r.language,
                "corpus_class": r.corpus_class,
                "n_components": r.n_components,
                "cumulative_variance": r.cumulative_variance,
                "sigma_drift": r.sigma_drift,
                "sigma_virtue": r.sigma_virtue,
                "mean_in_score": r.mean_in_score,
                "mean_out_score": r.mean_out_score,
                "effect_size": r.effect_size,
                "passed": r.passed,
            }
            for r in summary.reports
        ],
        "all_passed": summary.all_passed,
    }
    return json.dumps(data, indent=2)

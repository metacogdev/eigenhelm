"""Harness runner — corpus scanning, DynamicHelm evaluation, and aggregation.

Usage:
    from eigenhelm.harness import run_harness
    report = run_harness(before_dir, after_dir, eigenspace=model)
"""

from __future__ import annotations

import os
import statistics
from pathlib import Path

from scipy.stats import mannwhitneyu

from eigenhelm.harness.report import CorpusStats, HarnessReport
from eigenhelm.helm import DynamicHelm
from eigenhelm.helm.models import EvaluationRequest
from eigenhelm.models import EigenspaceModel
from eigenhelm.parsers.language_map import LANGUAGE_MAP

# Extension → language mapping
_EXT_TO_LANG: dict[str, str] = {ext: lang for lang, (_, ext) in LANGUAGE_MAP.items()}


def _discover_corpus_files(corpus_dir: Path) -> list[tuple[Path, str]]:
    """Walk a directory and return eligible (path, language) pairs."""
    results: list[tuple[Path, str]] = []
    for root, _, files in os.walk(corpus_dir, followlinks=False):
        for filename in files:
            child = Path(root) / filename
            if child.is_symlink():
                continue
            lang = _EXT_TO_LANG.get(child.suffix)
            if lang is not None:
                results.append((child, lang))
    return results


def run_corpus(corpus_dir: Path, helm: DynamicHelm) -> CorpusStats:
    """Evaluate all eligible files in a directory and aggregate statistics.

    Args:
        corpus_dir: Directory to scan for source files.
        helm: Configured DynamicHelm instance.

    Returns:
        CorpusStats with aggregate metrics.

    Raises:
        ValueError: If zero eligible files are found.
    """
    files = _discover_corpus_files(corpus_dir)
    if not files:
        raise ValueError(f"No eligible source files found in {corpus_dir}")

    scores: list[float] = []
    accepted = warned = rejected = n_skipped = 0

    for path, lang in files:
        try:
            source = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            n_skipped += 1
            continue

        result = helm.evaluate(
            EvaluationRequest(source=source, language=lang, file_path=str(path))
        )
        scores.append(result.score)
        if result.decision == "accept":
            accepted += 1
        elif result.decision == "warn":
            warned += 1
        elif result.decision == "reject":
            rejected += 1

    if not scores:
        raise ValueError(f"No evaluable files in {corpus_dir} (all skipped)")

    mean_score = statistics.mean(scores)
    median_score = statistics.median(scores)
    std_score = statistics.stdev(scores) if len(scores) > 1 else 0.0

    return CorpusStats(
        n_files=len(scores),
        n_skipped=n_skipped,
        mean_score=mean_score,
        median_score=median_score,
        std_score=std_score,
        accepted=accepted,
        warned=warned,
        rejected=rejected,
        scores=tuple(scores),
    )


def run_harness(
    before_dir: Path | str,
    after_dir: Path | str,
    *,
    eigenspace: EigenspaceModel | None = None,
) -> HarnessReport:
    """Run the evaluation harness: compare two corpora with Mann-Whitney U test.

    Args:
        before_dir: "Before" corpus directory.
        after_dir: "After" corpus directory.
        eigenspace: Optional pre-loaded eigenspace model.

    Returns:
        HarnessReport with statistics and significance test results.
    """
    before_dir = Path(before_dir)
    after_dir = Path(after_dir)

    helm = DynamicHelm(eigenspace=eigenspace)
    before_stats = run_corpus(before_dir, helm)
    after_stats = run_corpus(after_dir, helm)

    u_stat, p_val = mannwhitneyu(
        before_stats.scores,
        after_stats.scores,
        alternative="two-sided",
    )

    # Convert numpy scalars to native Python types for frozen dataclass
    u_stat = float(u_stat)
    p_val = float(p_val)
    delta = after_stats.mean_score - before_stats.mean_score
    significant = p_val < 0.05
    improvement = significant and delta < 0.0

    return HarnessReport(
        before=before_stats,
        after=after_stats,
        delta_mean_score=delta,
        u_statistic=u_stat,
        p_value=p_val,
        significant=significant,
        improvement=improvement,
    )

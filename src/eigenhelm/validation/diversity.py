"""Corpus diversity analysis (014-polyglot-discrimination).

Measures feature-space diversity across a language's training corpus to detect
narrow or homogeneous corpora before model training. Operates on the raw
69-dimensional design matrix with per-vector repo labels.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

import numpy as np


# --- Thresholds ---
THRESHOLD_EFFECTIVE_RANK = 3.0
THRESHOLD_MIN_CENTROID_DISTANCE = 1.0
THRESHOLD_BETWEEN_REPO_VARIANCE_RATIO = 0.01
THRESHOLD_DEAD_FEATURES = 10
THRESHOLD_SAMPLE_BALANCE = 0.1


@dataclass(frozen=True)
class RepoDiversityStats:
    """Per-repo diversity statistics."""

    repo_name: str
    n_vectors: int
    centroid_norm: float  # L2 norm of standardized centroid


@dataclass(frozen=True)
class DiversityReport:
    """Corpus diversity analysis result for a single language."""

    language: str
    corpus_class: str
    n_repos: int
    n_vectors: int
    n_features: int  # 69

    # Global metrics
    effective_rank: float
    dead_features: int
    explained_variance_top3: list[float]

    # Inter-repo metrics
    min_centroid_distance: float
    mean_centroid_distance: float
    between_repo_variance_ratio: float
    sample_balance: float

    # Per-repo breakdown
    repo_stats: list[RepoDiversityStats]

    # Verdicts
    passed: bool
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class DiversitySummary:
    """Aggregated diversity results across languages."""

    reports: tuple[DiversityReport, ...]

    @property
    def all_passed(self) -> bool:
        """True only if every report passed."""
        return all(r.passed for r in self.reports)


@dataclass(frozen=True)
class _RankMetrics:
    effective_rank: float
    explained_variance_top3: list[float]


@dataclass(frozen=True)
class _RepoGeometry:
    unique_repos: list[str]
    centroids: dict[str, np.ndarray]
    counts: dict[str, int]
    distances: list[float]


def run_diversity_analysis(
    X: np.ndarray,
    repo_labels: list[str],
    language: str,
    corpus_class: str = "A",
) -> DiversityReport:
    """Analyze corpus diversity from a design matrix and repo labels.

    Args:
        X: Design matrix, shape (N, 69).
        repo_labels: Repo name per row, length N.
        language: Language identifier (e.g., "go", "javascript").
        corpus_class: Corpus class identifier (default "A").

    Returns:
        DiversityReport with all metrics computed.

    Raises:
        ValueError: If X has wrong shape, contains NaN/Inf, or repo_labels
            length mismatches.
    """
    unique_repos = _validate_inputs(X, repo_labels)
    n_vectors, n_features = X.shape
    X_std, stds = _standardize(X)
    dead_features = _count_dead_features(stds)
    rank_metrics = _compute_rank_metrics(X_std)
    geometry = _compute_repo_geometry(X_std, repo_labels, unique_repos)
    min_centroid_distance, mean_centroid_distance = _distance_summary(
        geometry.distances
    )
    between_repo_variance_ratio = _between_repo_variance_ratio(X_std, geometry)
    sample_balance = _sample_balance(geometry.counts)
    repo_stats = _repo_stats(geometry)
    warnings = _diversity_warnings(
        rank_metrics.effective_rank,
        min_centroid_distance,
        between_repo_variance_ratio,
        dead_features,
        sample_balance,
    )

    return DiversityReport(
        language=language,
        corpus_class=corpus_class,
        n_repos=len(unique_repos),
        n_vectors=n_vectors,
        n_features=n_features,
        effective_rank=rank_metrics.effective_rank,
        dead_features=dead_features,
        explained_variance_top3=rank_metrics.explained_variance_top3,
        min_centroid_distance=min_centroid_distance,
        mean_centroid_distance=mean_centroid_distance,
        between_repo_variance_ratio=between_repo_variance_ratio,
        sample_balance=sample_balance,
        repo_stats=repo_stats,
        passed=len(warnings) == 0,
        warnings=warnings,
    )


def _validate_inputs(X: np.ndarray, repo_labels: list[str]) -> list[str]:
    if X.ndim != 2 or X.shape[1] != 69:
        msg = f"X must have shape (N, 69), got {X.shape}"
        raise ValueError(msg)
    if len(repo_labels) != X.shape[0]:
        msg = f"repo_labels length {len(repo_labels)} != X.shape[0] {X.shape[0]}"
        raise ValueError(msg)
    if not np.isfinite(X).all():
        msg = "X contains NaN or Inf values"
        raise ValueError(msg)

    unique_repos = sorted(set(repo_labels))
    if len(unique_repos) < 2:
        msg = f"Need at least 2 distinct repos, got {len(unique_repos)}"
        raise ValueError(msg)
    return unique_repos


def _standardize(X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    stds = np.std(X, axis=0, ddof=0)
    means = np.mean(X, axis=0)
    safe_stds = np.where(stds > 1e-12, stds, 1.0)
    return (X - means) / safe_stds, stds


def _count_dead_features(stds: np.ndarray) -> int:
    return int(np.sum(stds < 1e-6))


def _compute_rank_metrics(X_std: np.ndarray) -> _RankMetrics:
    _, s, _ = np.linalg.svd(X_std, full_matrices=False)
    s_sq = s**2
    total = s_sq.sum()
    if total <= 0:
        return _RankMetrics(0.0, [0.0, 0.0, 0.0])

    evr = s_sq / total
    evr_pos = evr[evr > 0]
    entropy = -np.sum(evr_pos * np.log(evr_pos))
    explained_variance_top3 = [float(v) for v in evr[:3]]
    explained_variance_top3 += [0.0] * (3 - len(explained_variance_top3))
    return _RankMetrics(
        effective_rank=float(np.exp(entropy)),
        explained_variance_top3=explained_variance_top3,
    )


def _compute_repo_geometry(
    X_std: np.ndarray,
    repo_labels: list[str],
    unique_repos: list[str],
) -> _RepoGeometry:
    centroids: dict[str, np.ndarray] = {}
    counts: dict[str, int] = {}
    for repo in unique_repos:
        mask = np.array([r == repo for r in repo_labels])
        repo_vectors = X_std[mask]
        centroids[repo] = np.mean(repo_vectors, axis=0)
        counts[repo] = int(mask.sum())

    return _RepoGeometry(
        unique_repos=unique_repos,
        centroids=centroids,
        counts=counts,
        distances=_centroid_distances(unique_repos, centroids),
    )


def _centroid_distances(
    unique_repos: list[str], centroids: dict[str, np.ndarray]
) -> list[float]:
    centroid_list = [centroids[r] for r in unique_repos]
    distances = []
    for i in range(len(centroid_list)):
        for j in range(i + 1, len(centroid_list)):
            distances.append(float(np.linalg.norm(centroid_list[i] - centroid_list[j])))
    return distances


def _distance_summary(distances: list[float]) -> tuple[float, float]:
    if not distances:
        return 0.0, 0.0
    return min(distances), float(np.mean(distances))


def _between_repo_variance_ratio(
    X_std: np.ndarray,
    geometry: _RepoGeometry,
) -> float:
    global_mean = np.mean(X_std, axis=0)
    total_var_per_feat = np.var(X_std, axis=0, ddof=0)
    between_var_per_feat = np.zeros(X_std.shape[1])
    for repo in geometry.unique_repos:
        diff = geometry.centroids[repo] - global_mean
        between_var_per_feat += geometry.counts[repo] * (diff**2)
    between_var_per_feat /= X_std.shape[0]

    total_var_sum = total_var_per_feat.sum()
    if total_var_sum <= 0:
        return 0.0
    return float(between_var_per_feat.sum() / total_var_sum)


def _sample_balance(counts_by_repo: dict[str, int]) -> float:
    counts = list(counts_by_repo.values())
    return min(counts) / max(counts) if max(counts) > 0 else 0.0


def _repo_stats(geometry: _RepoGeometry) -> list[RepoDiversityStats]:
    return [
        RepoDiversityStats(
            repo_name=repo,
            n_vectors=geometry.counts[repo],
            centroid_norm=float(np.linalg.norm(geometry.centroids[repo])),
        )
        for repo in geometry.unique_repos
    ]


def _diversity_warnings(
    effective_rank: float,
    min_centroid_distance: float,
    between_repo_variance_ratio: float,
    dead_features: int,
    sample_balance: float,
) -> list[str]:
    checks = [
        (
            effective_rank < THRESHOLD_EFFECTIVE_RANK,
            f"effective_rank {effective_rank:.2f} < {THRESHOLD_EFFECTIVE_RANK}",
        ),
        (
            min_centroid_distance < THRESHOLD_MIN_CENTROID_DISTANCE,
            f"min_centroid_distance {min_centroid_distance:.2f} < "
            f"{THRESHOLD_MIN_CENTROID_DISTANCE}",
        ),
        (
            between_repo_variance_ratio < THRESHOLD_BETWEEN_REPO_VARIANCE_RATIO,
            f"between_repo_variance_ratio {between_repo_variance_ratio:.4f} < "
            f"{THRESHOLD_BETWEEN_REPO_VARIANCE_RATIO}",
        ),
        (
            dead_features > THRESHOLD_DEAD_FEATURES,
            f"dead_features {dead_features} > {THRESHOLD_DEAD_FEATURES}",
        ),
        (
            sample_balance < THRESHOLD_SAMPLE_BALANCE,
            f"sample_balance {sample_balance:.2f} < {THRESHOLD_SAMPLE_BALANCE}",
        ),
    ]
    return [message for failed, message in checks if failed]


def render_human(summary: DiversitySummary) -> str:
    """Render a human-readable diversity report table."""
    header = (
        f"{'Language':<12} {'Repos':>5} {'Vectors':>7} {'Eff.Rank':>8} "
        f"{'Dead':>4} {'MinDist':>7} {'BtwVar':>6} {'Balance':>7} {'Pass':>5}"
    )
    sep = "-" * len(header)

    rows: list[str] = []
    for r in summary.reports:
        status = "PASS" if r.passed else "FAIL"
        rows.append(
            f"{r.language:<12} {r.n_repos:>5} {r.n_vectors:>7} "
            f"{r.effective_rank:>8.2f} {r.dead_features:>4} "
            f"{r.min_centroid_distance:>7.2f} "
            f"{r.between_repo_variance_ratio:>6.4f} "
            f"{r.sample_balance:>7.2f} {status:>5}"
        )

    overall = "ALL PASSED" if summary.all_passed else "SOME FAILED"
    return "\n".join(
        [
            "Corpus Diversity Report",
            sep,
            header,
            sep,
            *rows,
            sep,
            f"Overall: {overall}",
        ]
    )


def render_json(summary: DiversitySummary) -> str:
    """Render a machine-parseable JSON diversity report."""
    languages: dict = {}
    for r in summary.reports:
        languages[r.language] = {
            "effective_rank": r.effective_rank,
            "dead_features": r.dead_features,
            "min_centroid_distance": r.min_centroid_distance,
            "between_repo_variance_ratio": r.between_repo_variance_ratio,
            "sample_balance": r.sample_balance,
            "passed": r.passed,
            "warnings": r.warnings,
            "repos": [
                {
                    "repo_name": rs.repo_name,
                    "n_vectors": rs.n_vectors,
                    "centroid_norm": rs.centroid_norm,
                }
                for rs in r.repo_stats
            ],
        }

    data = {
        "version": "014-polyglot-discrimination",
        "languages": languages,
        "summary": {
            "passed_count": sum(1 for r in summary.reports if r.passed),
            "total": len(summary.reports),
        },
    }
    return json.dumps(data, indent=2)

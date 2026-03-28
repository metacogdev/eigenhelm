"""PCA feature decomposition and direct attribution for scoring dimensions.

Decomposes manifold_drift and manifold_alignment back to per-feature
contributions via PCA math. Provides direct attribution for
information-theoretic dimensions (entropy, compression, NCD).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from eigenhelm.attribution.constants import FEATURE_NAMES
from eigenhelm.attribution.models import (
    DimensionAttribution,
    DirectAttribution,
    FeatureContribution,
)

if TYPE_CHECKING:
    from eigenhelm.critic import AestheticMetrics
    from eigenhelm.models import EigenspaceModel, FeatureVector, ProjectionResult

NDIM = 69


def _build_feature_contributions(
    values: np.ndarray,
    feature_vector: FeatureVector,
    model: EigenspaceModel,
    top_n: int,
) -> tuple[FeatureContribution, ...]:
    """Build ranked FeatureContribution tuples from a per-feature value array."""
    magnitudes = np.abs(values)
    # Get indices sorted by magnitude descending
    ranked_indices = np.argsort(magnitudes)[::-1][:top_n]

    contributions = []
    for rank_0, idx in enumerate(ranked_indices):
        idx_int = int(idx)
        raw = float(feature_vector.values[idx_int])
        mean = float(model.mean[idx_int])
        std = float(model.std[idx_int])
        contributions.append(
            FeatureContribution(
                feature_index=idx_int,
                feature_name=FEATURE_NAMES[idx_int],
                contribution_value=float(values[idx_int]),
                contribution_magnitude=float(magnitudes[idx_int]),
                raw_value=raw,
                corpus_mean=mean,
                standardized_deviation=(raw - mean) / std,
                rank=rank_0 + 1,
            )
        )
    return tuple(contributions)


def decompose_drift(
    projection: ProjectionResult,
    model: EigenspaceModel,
    feature_vector: FeatureVector,
    top_n: int = 3,
) -> DimensionAttribution:
    """Decompose manifold_drift into per-feature reconstruction error contributions.

    contribution_value[i] = x_rec[i] - x_norm[i]  (per-feature reconstruction error)
    Σ contribution_value[i]² = L_drift²  (exact decomposition)
    """
    normalized_score = min(max(projection.l_drift / model.sigma_drift, 0.0), 1.0)

    if projection.x_norm is None or projection.x_rec is None:
        return DimensionAttribution(
            dimension="manifold_drift",
            normalized_score=normalized_score,
            available=False,
            method="pca_reconstruction",
        )

    error = projection.x_rec - projection.x_norm  # shape (69,)
    features = _build_feature_contributions(error, feature_vector, model, top_n)

    return DimensionAttribution(
        dimension="manifold_drift",
        normalized_score=normalized_score,
        available=True,
        method="pca_reconstruction",
        features=features,
    )


def decompose_alignment(
    projection: ProjectionResult,
    model: EigenspaceModel,
    feature_vector: FeatureVector,
    top_n: int = 3,
) -> DimensionAttribution:
    """Decompose manifold_alignment via coordinate-weighted back-projection.

    c[i] = Σⱼ z[j] · W[i,j]  (back-projection to feature space)
    This is a ranking heuristic, not an exact additive decomposition.
    """
    normalized_score = min(max(projection.l_virtue / model.sigma_virtue, 0.0), 1.0)

    if projection.coordinates is None:
        return DimensionAttribution(
            dimension="manifold_alignment",
            normalized_score=normalized_score,
            available=False,
            method="pca_alignment",
        )

    z = projection.coordinates
    W = model.projection_matrix
    c = z @ W.T  # shape (69,) — back-projection

    features = _build_feature_contributions(c, feature_vector, model, top_n)

    return DimensionAttribution(
        dimension="manifold_alignment",
        normalized_score=normalized_score,
        available=True,
        method="pca_alignment",
        features=features,
    )


# Direct attribution metric configs
_DIRECT_CONFIGS: dict[str, tuple[str, str, str]] = {
    # dimension -> (metric_name, normalization, metrics_attr)
    "token_entropy": ("shannon_entropy", "1.0 - (H / 8.0)", "entropy"),
    "compression_structure": (
        "birkhoff_measure",
        "birkhoff_direct",
        "birkhoff_measure",
    ),
    "ncd_exemplar_distance": ("ncd", "ncd_direct", ""),
}


def attribute_direct(
    dimension: str,
    metrics: AestheticMetrics,
    normalized_values: dict[str, float],
    nearest_exemplar_id: str | None = None,
) -> DimensionAttribution:
    """Provide direct attribution for information-theoretic dimensions.

    These dimensions are NOT part of the 69-dim feature vector — they are
    computed independently over the full source string.
    """
    normalized_score = normalized_values.get(dimension, 0.0)
    normalized_score = min(max(normalized_score, 0.0), 1.0)

    config = _DIRECT_CONFIGS.get(dimension)
    if config is None:
        return DimensionAttribution(
            dimension=dimension,
            normalized_score=normalized_score,
            available=False,
            method="direct",
        )

    metric_name, normalization, metrics_attr = config

    # NCD requires exemplar to be available
    if dimension == "ncd_exemplar_distance" and nearest_exemplar_id is None:
        return DimensionAttribution(
            dimension=dimension,
            normalized_score=normalized_score,
            available=False,
            method="direct",
        )

    # Get computed value from metrics
    if dimension == "ncd_exemplar_distance":
        computed_value = normalized_score  # NCD normalized value IS the distance
    else:
        computed_value = float(getattr(metrics, metrics_attr))

    direct = DirectAttribution(
        metric_name=metric_name,
        computed_value=computed_value,
        normalization=normalization,
        normalized_score=normalized_score,
        exemplar_id=nearest_exemplar_id
        if dimension == "ncd_exemplar_distance"
        else None,
    )

    return DimensionAttribution(
        dimension=dimension,
        normalized_score=normalized_score,
        available=True,
        method="direct",
        direct=direct,
    )

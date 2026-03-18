"""PCA eigenspace projection with L_drift and L_virtue loss calculations.

Projection formula:
  x_norm = (x - μ) / σ         (standardize)
  z      = x_norm @ W           (project to k-dim PC space)
  x_rec  = z @ W.T              (reconstruct in normalized space)
  L_drift  = ||x_rec - x_norm||₂  (orthogonal distance from manifold)
  L_virtue = ||z||₂              (distance from elite centroid / origin)

quality_flag thresholds:
  "high_drift"    if L_drift > HIGH_DRIFT_SIGMA * σ_drift
  "partial_input" if source FeatureVector has partial_parse=True
  "nominal"       otherwise

Reference: Jolliffe, I.T. (2002). Principal Component Analysis. Springer.
"""

from __future__ import annotations

import numpy as np

from eigenhelm.models import EigenspaceModel, FeatureVector, ProjectionResult

# L_drift quality threshold: flag if drift > 2 standard deviations
# (approximated at runtime from the reconstruction error magnitude).
_HIGH_DRIFT_RATIO = 2.0


def project(vector: FeatureVector, model: EigenspaceModel) -> ProjectionResult:
    """Project a FeatureVector into the PCA eigenspace.

    Args:
        vector: A FeatureVector from VirtueExtractor.extract().
        model: A loaded EigenspaceModel.

    Returns:
        ProjectionResult with coordinates, l_drift, l_virtue, quality_flag.

    Raises:
        ValueError: If feature vector dimension doesn't match model.
    """
    x = vector.values  # shape (69,)

    if x.shape[0] != model.projection_matrix.shape[0]:
        raise ValueError(
            f"Feature vector dim {x.shape[0]} != model input dim {model.projection_matrix.shape[0]}"
        )

    W = model.projection_matrix  # (69, k)
    mu = model.mean  # (69,)
    sigma = model.std  # (69,)

    # Standardize.
    x_norm = (x - mu) / sigma  # (69,)

    # Project to PC space.
    z = x_norm @ W  # (k,)

    # Reconstruct in normalized space.
    x_rec = z @ W.T  # (69,)

    # Losses.
    l_drift = float(np.linalg.norm(x_rec - x_norm))
    l_virtue = float(np.linalg.norm(z))

    # Quality flag.
    if vector.partial_parse:
        quality_flag = "partial_input"
    elif l_drift > _HIGH_DRIFT_RATIO * _drift_threshold(W, sigma):
        quality_flag = "high_drift"
    else:
        quality_flag = "nominal"

    return ProjectionResult(
        coordinates=z,
        l_drift=l_drift,
        l_virtue=l_virtue,
        quality_flag=quality_flag,
        x_norm=x_norm,
        x_rec=x_rec,
    )


def _drift_threshold(W: np.ndarray, sigma: np.ndarray) -> float:
    """Estimate the expected L_drift for a typical in-distribution point.

    Uses the Frobenius norm of the null-space projection (I - W @ W^T)
    weighted by the feature standard deviations as a scale reference.
    This gives a data-independent but dimensionally consistent threshold.
    """
    d = W.shape[0]
    null_proj = np.eye(d) - W @ W.T  # (d, d)
    # Expected residual scale: how much variance is lost in projection.
    residual_var = np.trace(null_proj * np.outer(sigma, sigma))
    return float(np.sqrt(max(residual_var, 1e-8)))

"""Deterministic PCA via economy SVD with sign-flip reproducibility convention."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from eigenhelm.models import CalibrationStats


def standardize(
    X: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Center and standardize design matrix using Bessel's correction (ddof=1).

    Args:
        X: Design matrix of shape (N, 69), dtype float64.

    Returns:
        (X_std, mean, std) where:
            X_std — standardized matrix, shape (N, 69)
            mean  — column means, shape (69,)
            std   — column stds (ddof=1), shape (69,), floored at 1e-10
    """
    mean = X.mean(axis=0)
    std = X.std(axis=0, ddof=1)
    std[std < 1e-10] = 1.0  # guard constant features (avoid division by zero)
    X_std = (X - mean) / std
    return X_std, mean, std


def compute_pca(
    X: np.ndarray,
    n_components: int | None = None,
    variance_threshold: float = 0.90,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Compute deterministic PCA via economy SVD.

    Args:
        X: Design matrix of shape (N, 69), dtype float64.
        n_components: Explicit component count. If None, auto-select via threshold.
        variance_threshold: Minimum cumulative explained variance for auto-select.

    Returns:
        (W, mean, std, explained_variance_ratio) where:
            W    — projection matrix, shape (69, k)
            mean — column means from standardize(), shape (69,)
            std  — column stds from standardize(), shape (69,)
            explained_variance_ratio — per-component ratios, shape (k,)

    Raises:
        ValueError: If n_components >= min(n_samples, n_features).
    """
    n_samples, n_features = X.shape
    max_components = min(n_samples - 1, n_features)

    if n_components is not None and n_components >= min(n_samples, n_features):
        raise ValueError(
            f"n_components={n_components} must be < min(n_samples={n_samples}, "
            f"n_features={n_features})={min(n_samples, n_features)}"
        )

    X_std, mean, std = standardize(X)

    # Economy SVD: U(N,p), s(p,), Vt(p,69) where p = min(N, 69)
    _U, s, Vt = np.linalg.svd(X_std, full_matrices=False)

    # Sign-flip convention (R2): for each row of Vt, ensure element with
    # largest absolute value is positive → cross-platform reproducibility
    max_abs_idx = np.argmax(np.abs(Vt), axis=1)
    signs = np.sign(Vt[np.arange(Vt.shape[0]), max_abs_idx])
    Vt *= signs[:, np.newaxis]

    # Explained variance: s² / (n-1) per R4 (matches ddof=1 from standardize)
    explained_var = (s**2) / (n_samples - 1)
    explained_ratio = explained_var / explained_var.sum()
    cumulative = np.cumsum(explained_ratio)

    if n_components is None:
        # Auto-select: first k where cumulative variance >= threshold
        k = int(np.searchsorted(cumulative, variance_threshold) + 1)
        k = min(k, max_components)
    else:
        k = n_components

    # W = Vt[:k].T — shape (69, k)
    W = Vt[:k].T
    return W, mean, std, explained_ratio[:k]


def compute_calibration(
    X: np.ndarray,
    W: np.ndarray,
    mean: np.ndarray,
    std: np.ndarray,
    percentile: float = 95.0,
) -> CalibrationStats:
    """Compute manifold normalization calibration constants from training corpus.

    Derives sigma_drift (p95 of reconstruction error) and sigma_virtue
    (p95 of PC-space L2 norm) from the training design matrix.
    Reference: Jolliffe (2002), Chapter 2 — PCA projection error.

    Args:
        X:          Design matrix, shape (N, 69), dtype float64. Raw (unstandardized).
        W:          Projection matrix, shape (69, k), dtype float64.
        mean:       Column means from standardize(), shape (69,).
        std:        Column stds from standardize(), shape (69,), all > 0.
        percentile: Percentile for calibration (default 95.0).

    Returns:
        CalibrationStats with sigma_drift > 0 and sigma_virtue > 0.
    """
    from eigenhelm.models import CalibrationStats

    X_std = (X - mean) / std  # shape (N, 69)
    Z = X_std @ W  # shape (N, k)  — PC coordinates
    X_rec = Z @ W.T  # shape (N, 69) — reconstruction

    l_drift_values = np.linalg.norm(X_rec - X_std, axis=1)  # shape (N,)
    l_virtue_values = np.linalg.norm(Z, axis=1)  # shape (N,)

    # Apply a floor to prevent zero sigma when all projections are identical
    # (e.g., all-empty-file corpus). 1e-8 << any real corpus spread.
    sigma_drift = max(float(np.percentile(l_drift_values, percentile)), 1e-8)
    sigma_virtue = max(float(np.percentile(l_virtue_values, percentile)), 1e-8)

    return CalibrationStats(
        sigma_drift=sigma_drift,
        sigma_virtue=sigma_virtue,
        n_projections=len(X),
        percentile=percentile,
    )

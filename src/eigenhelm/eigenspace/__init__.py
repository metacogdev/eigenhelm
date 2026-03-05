"""PCA eigenspace loader and projection."""

from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np

from eigenhelm.models import FEATURE_DIM, EigenspaceModel


def load_model(path: str | Path) -> EigenspaceModel:
    """Load a pre-trained PCA eigenspace model from a .npz file.

    Expected .npz keys:
      projection_matrix  — shape (69, k), float64
      mean               — shape (69,),   float64
      std                — shape (69,),   float64
      n_components       — scalar int
      version            — scalar str (e.g., "1.0.0")
      corpus_hash        — scalar str (SHA-256 of training corpus)
      sigma_drift        — scalar float64 (p95 l_drift; optional, added in 0.2.0)
      sigma_virtue       — scalar float64 (p95 l_virtue; optional, added in 0.2.0)

    Args:
        path: Path to the .npz model file.

    Returns:
        EigenspaceModel ready for projection.

    Raises:
        FileNotFoundError: If path does not exist.
        KeyError: If a required key is missing.
        ValueError: If matrix dimensions are invalid.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Eigenspace model not found: {path}")

    data = np.load(path, allow_pickle=True)

    required = ("projection_matrix", "mean", "std")
    for key in required:
        if key not in data:
            raise KeyError(f"Missing key {key!r} in eigenspace model {path}")

    n_components = (
        int(data["n_components"])
        if "n_components" in data
        else (data["projection_matrix"].shape[1])
    )
    version = str(data["version"]) if "version" in data else "unknown"
    corpus_hash = str(data["corpus_hash"]) if "corpus_hash" in data else "unknown"

    if "sigma_drift" in data and "sigma_virtue" in data:
        sigma_drift = float(data["sigma_drift"])
        sigma_virtue = float(data["sigma_virtue"])
    else:
        warnings.warn(
            f"Model '{path}' has no calibration data; scoring falls back to "
            "sigma_drift=1.0, sigma_virtue=1.0. "
            "Re-train the model to enable calibrated scoring.",
            stacklevel=2,
        )
        sigma_drift = 1.0
        sigma_virtue = 1.0

    return EigenspaceModel(
        projection_matrix=data["projection_matrix"].astype(np.float64),
        mean=data["mean"].astype(np.float64),
        std=data["std"].astype(np.float64),
        n_components=n_components,
        version=version,
        corpus_hash=corpus_hash,
        sigma_drift=sigma_drift,
        sigma_virtue=sigma_virtue,
    )


def make_synthetic_model(
    n_components: int = 3,
    seed: int = 42,
) -> EigenspaceModel:
    """Create a synthetic EigenspaceModel for testing.

    Uses a random orthonormal projection matrix so projection math
    can be validated independent of real corpus data.

    Args:
        n_components: Number of principal components (k).
        seed: Random seed for reproducibility.

    Returns:
        EigenspaceModel with valid but synthetic values.
    """
    rng = np.random.default_rng(seed)

    # Random orthonormal matrix via QR decomposition.
    raw = rng.standard_normal((FEATURE_DIM, n_components))
    W, _ = np.linalg.qr(raw)
    W = W[:, :n_components]

    mean = rng.standard_normal(FEATURE_DIM)
    std = np.abs(rng.standard_normal(FEATURE_DIM)) + 0.1  # ensure > 0

    return EigenspaceModel(
        projection_matrix=W,
        mean=mean,
        std=std,
        n_components=n_components,
        version="synthetic-test",
        corpus_hash="0000000000000000",
    )

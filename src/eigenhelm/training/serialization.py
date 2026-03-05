"""Serialization helpers: write .npz eigenspace model files."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from eigenhelm.models import TrainingResult


def save_model(result: TrainingResult, path: Path, *, force: bool = False) -> None:
    """Serialize a TrainingResult to a .npz file with 9 keys.

    Keys written:
        projection_matrix, mean, std, n_components, version, corpus_hash
        (from EigenspaceModel) + explained_variance_ratio (metadata)
        + sigma_drift, sigma_virtue (calibration constants).

    Args:
        result: Output of train_eigenspace().
        path: Output file path.
        force: If True, overwrite existing file. If False and file exists,
            raises FileExistsError.

    Raises:
        FileExistsError: If path exists and force is False.
    """
    path = Path(path)
    if path.exists() and not force:
        raise FileExistsError(f"Output file already exists: {path}. Use force=True to overwrite.")
    model = result.model
    np.savez(
        path,
        projection_matrix=model.projection_matrix,
        mean=model.mean,
        std=model.std,
        n_components=np.array(model.n_components),
        version=np.array(model.version),
        corpus_hash=np.array(model.corpus_hash),
        explained_variance_ratio=result.explained_variance_ratio,
        sigma_drift=np.array(model.sigma_drift),
        sigma_virtue=np.array(model.sigma_virtue),
    )

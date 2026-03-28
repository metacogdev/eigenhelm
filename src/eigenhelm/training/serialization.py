"""Serialization helpers: write .npz eigenspace model files."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from eigenhelm.models import TrainingResult


def save_model(result: TrainingResult, path: Path, *, force: bool = False) -> None:
    """Serialize a TrainingResult to a .npz file.

    Keys written:
        projection_matrix, mean, std, n_components, version, corpus_hash
        (from EigenspaceModel) + explained_variance_ratio (metadata)
        + sigma_drift, sigma_virtue (calibration constants)
        + n_exemplars, exemplar_blob, exemplar_offsets, exemplar_hashes,
          exemplar_clusters (exemplar data, when present).

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
        raise FileExistsError(
            f"Output file already exists: {path}. Use force=True to overwrite."
        )
    model = result.model

    arrays: dict[str, np.ndarray] = {
        "projection_matrix": model.projection_matrix,
        "mean": model.mean,
        "std": model.std,
        "n_components": np.array(model.n_components),
        "version": np.array(model.version),
        "corpus_hash": np.array(model.corpus_hash),
        "explained_variance_ratio": result.explained_variance_ratio,
        "sigma_drift": np.array(model.sigma_drift),
        "sigma_virtue": np.array(model.sigma_virtue),
    }

    # Always write n_training_files (useful even without language metadata)
    arrays["n_training_files"] = np.array(model.n_training_files)

    # Write language/corpus_class metadata when language is set (009+)
    if model.language is not None:
        arrays["language"] = np.array(model.language)
        arrays["corpus_class"] = np.array(model.corpus_class or "A")

    # Serialize exemplars using blob+offsets approach (zero-pickle)
    if model.exemplars:
        blobs = [e.compressed_content for e in model.exemplars]
        offsets = np.zeros(len(blobs) + 1, dtype=np.int64)
        for i, b in enumerate(blobs):
            offsets[i + 1] = offsets[i] + len(b)
        concatenated = b"".join(blobs)

        arrays["n_exemplars"] = np.array(len(model.exemplars))
        arrays["exemplar_blob"] = np.frombuffer(concatenated, dtype=np.uint8)
        arrays["exemplar_offsets"] = offsets
        arrays["exemplar_hashes"] = np.array([e.content_hash for e in model.exemplars])
        arrays["exemplar_clusters"] = np.array([e.cluster for e in model.exemplars])
    else:
        arrays["n_exemplars"] = np.array(0)

    # 015: Write calibrated thresholds and score distribution
    if model.calibrated_accept is not None:
        arrays["calibrated_accept"] = np.array(
            model.calibrated_accept, dtype=np.float64
        )
        arrays["calibrated_reject"] = np.array(
            model.calibrated_reject, dtype=np.float64
        )
    if model.score_distribution is not None:
        sd = model.score_distribution
        arrays["score_dist_min"] = np.array(sd.min, dtype=np.float64)
        arrays["score_dist_p10"] = np.array(sd.p10, dtype=np.float64)
        arrays["score_dist_p25"] = np.array(sd.p25, dtype=np.float64)
        arrays["score_dist_median"] = np.array(sd.median, dtype=np.float64)
        arrays["score_dist_p75"] = np.array(sd.p75, dtype=np.float64)
        arrays["score_dist_p90"] = np.array(sd.p90, dtype=np.float64)
        arrays["score_dist_max"] = np.array(sd.max, dtype=np.float64)
        arrays["score_dist_n_scores"] = np.array(sd.n_scores)

    np.savez(path, **arrays)

"""Training pipeline public API: train_eigenspace(), save_model(), inspect_model()."""

from __future__ import annotations

from pathlib import Path

from eigenhelm.models import TrainingResult

__all__ = [
    "train_eigenspace",
    "save_model",
    "inspect_model",
    "get_package_version",
    "TrainingResult",
]


def get_package_version() -> str:
    """Return the installed eigenhelm package version, falling back to '0.0.0-dev'."""
    from importlib.metadata import PackageNotFoundError, version

    try:
        return version("eigenhelm")
    except PackageNotFoundError:
        return "0.0.0-dev"


def train_eigenspace(
    corpus_dir: Path,
    *,
    n_components: int | None = None,
    variance_threshold: float = 0.90,
    version: str | None = None,
) -> TrainingResult:
    """Train a PCA eigenspace model from a code corpus.

    Raises:
        FileNotFoundError: If corpus_dir does not exist.
        ValueError: If corpus contains zero eligible files, all extractions fail,
            n_components >= min(n_samples, n_features), or variance_threshold not in (0.0, 1.0].
    """
    import warnings

    import numpy as np

    from eigenhelm.models import EigenspaceModel
    from eigenhelm.training.corpus import (
        EXTENSION_TO_LANGUAGE,
        compute_corpus_hash,
        discover_corpus_files,
    )
    from eigenhelm.training.pca import compute_calibration, compute_pca
    from eigenhelm.virtue_extractor import VirtueExtractor

    corpus_dir = Path(corpus_dir)
    if not corpus_dir.exists():
        raise FileNotFoundError(f"Corpus directory not found: {corpus_dir}")

    # US2 validation (T017): variance_threshold range
    if not (0.0 < variance_threshold <= 1.0):
        raise ValueError(f"variance_threshold must be in (0.0, 1.0], got {variance_threshold}")

    # Discover eligible files
    files = discover_corpus_files(corpus_dir)
    if not files:
        raise ValueError(f"No eligible code files found in corpus directory: {corpus_dir}")

    corpus_hash = compute_corpus_hash(files)
    extractor = VirtueExtractor()

    vectors = []
    n_files_processed = 0
    n_files_skipped = 0

    for f in files:
        try:
            source = f.read_text(encoding="utf-8", errors="replace")
            language = EXTENSION_TO_LANGUAGE[f.suffix]
            file_vectors = extractor.extract(source, language)
            if file_vectors:
                vectors.extend(fv.values for fv in file_vectors)
                n_files_processed += 1
            else:
                n_files_skipped += 1
        except Exception as exc:
            warnings.warn(
                f"Skipping {f.name}: feature extraction failed: {exc}",
                stacklevel=2,
            )
            n_files_skipped += 1

    if not vectors:
        raise ValueError("All feature extractions failed — no valid vectors to train on.")

    # Assemble design matrix and exclude NaN/Inf vectors (FR-013)
    X_raw = np.stack(vectors, axis=0)  # shape (N, 69)
    valid_mask = np.all(np.isfinite(X_raw), axis=1)
    n_vectors_excluded = int((~valid_mask).sum())
    if n_vectors_excluded > 0:
        warnings.warn(
            f"Excluded {n_vectors_excluded} vector(s) containing NaN or Inf values.",
            stacklevel=2,
        )
    X = X_raw[valid_mask]

    # US2 guard (T019): must have at least some valid vectors
    if X.shape[0] == 0:
        raise ValueError(
            "All feature extractions failed — no valid vectors remain after NaN/Inf exclusion."
        )

    # Compute PCA (T011 raises ValueError if n_components is invalid)
    W, mean, std, explained_ratio = compute_pca(X, n_components, variance_threshold)
    k = W.shape[1]
    cumulative_variance = float(explained_ratio.sum())

    # Compute calibration constants from the training distribution
    calibration = compute_calibration(X, W, mean, std)

    resolved_version = version if version is not None else get_package_version()

    model = EigenspaceModel(
        projection_matrix=W,
        mean=mean,
        std=std,
        n_components=k,
        version=resolved_version,
        corpus_hash=corpus_hash,
        sigma_drift=calibration.sigma_drift,
        sigma_virtue=calibration.sigma_virtue,
    )

    return TrainingResult(
        model=model,
        explained_variance_ratio=explained_ratio,
        cumulative_variance=cumulative_variance,
        n_files_processed=n_files_processed,
        n_files_skipped=n_files_skipped,
        n_units_extracted=len(vectors),
        n_vectors_excluded=n_vectors_excluded,
        calibration=calibration,
    )


def save_model(result: TrainingResult, path: Path, *, force: bool = False) -> None:
    """Serialize a TrainingResult to a .npz file.

    Raises:
        FileExistsError: If path exists and force is False.
    """
    from eigenhelm.training.serialization import save_model as _save

    return _save(result, path, force=force)


def inspect_model(path: Path) -> dict:
    """Load a .npz file and return inspection metadata dict.

    Raises:
        FileNotFoundError: If path does not exist.
        KeyError: If required keys are missing from the .npz file.
    """
    import numpy as np

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Model file not found: {path}")

    data = np.load(path, allow_pickle=False)

    # These keys are required — raise KeyError if missing
    required = ("projection_matrix", "mean", "std", "n_components", "version", "corpus_hash")
    for key in required:
        if key not in data:
            raise KeyError(f"Required key missing from model file: {key!r}")

    W = data["projection_matrix"]
    mean = data["mean"]
    std = data["std"]
    n_components = int(data["n_components"])
    version = str(data["version"])
    corpus_hash = str(data["corpus_hash"])

    # explained_variance_ratio is optional (backward-compatible)
    if "explained_variance_ratio" in data:
        evr = data["explained_variance_ratio"]
        cumulative_variance = float(evr.sum())
    else:
        evr = None
        cumulative_variance = float("nan")

    sigma_drift = float(data["sigma_drift"]) if "sigma_drift" in data else None
    sigma_virtue = float(data["sigma_virtue"]) if "sigma_virtue" in data else None

    return {
        "n_components": n_components,
        "explained_variance_ratio": evr,
        "cumulative_variance": cumulative_variance,
        "corpus_hash": corpus_hash,
        "version": version,
        "mean_range": (float(mean.min()), float(mean.max())),
        "std_range": (float(std.min()), float(std.max())),
        "projection_shape": (int(W.shape[0]), int(W.shape[1])),
        "sigma_drift": sigma_drift,
        "sigma_virtue": sigma_virtue,
    }

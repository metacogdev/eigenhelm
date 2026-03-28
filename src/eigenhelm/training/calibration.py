"""Training-time score distribution computation and threshold calibration.

Computes the aesthetic score distribution over a training corpus and derives
percentile-based accept/reject thresholds. Stored in the .npz model file
so that evaluation-time classification is calibrated per model.
"""

from __future__ import annotations

import warnings

import numpy as np

from eigenhelm.models import CalibrationThresholds, EigenspaceModel, ScoreDistribution

# Minimum scored vectors required for reliable percentile estimation.
MIN_SCORES_FOR_CALIBRATION = 10


def compute_score_distribution(
    X: np.ndarray,
    model: EigenspaceModel,
    source_bytes_list: list[bytes],
) -> ScoreDistribution:
    """Score every training vector through AestheticCritic and compute distribution.

    For each training vector, projects through the model's eigenspace, then
    evaluates with AestheticCritic using the model's sigma values and exemplars.
    Collects all aesthetic loss scores and computes percentile statistics.

    Args:
        X: Design matrix of shape (N, 69), standardized feature vectors.
        model: Fully constructed EigenspaceModel with projection_matrix, mean,
            std, sigma_drift, sigma_virtue, and optionally exemplars.
        source_bytes_list: List of N encoded source byte strings corresponding
            to each row of X (used for NCD computation via exemplars).

    Returns:
        ScoreDistribution with min, p10, p25, median, p75, p90, max, n_scores.

    Raises:
        ValueError: If fewer than MIN_SCORES_FOR_CALIBRATION vectors produce
            valid scores.
    """
    import zlib

    from eigenhelm.critic import AestheticCritic
    from eigenhelm.models import ProjectionResult

    # Decompress exemplars for NCD (same pattern as DynamicHelm.__init__)
    exemplar_bytes = None
    if model.exemplars is not None:
        exemplar_bytes = [
            zlib.decompress(e.compressed_content) for e in model.exemplars
        ]

    critic = AestheticCritic(
        sigma_drift=model.sigma_drift,
        sigma_virtue=model.sigma_virtue,
        exemplars=exemplar_bytes,
    )

    # Pre-compute projection constants
    W = model.projection_matrix
    mean = model.mean
    std = model.std

    scores: list[float] = []
    for i in range(X.shape[0]):
        try:
            # Standardize and project (same math as eigenspace.project)
            x_std = (X[i] - mean) / std
            z = x_std @ W  # PC coordinates
            x_rec = z @ W.T  # reconstructed in standardized space
            l_drift = float(np.linalg.norm(x_rec - x_std))
            l_virtue = float(np.linalg.norm(z))

            projection = ProjectionResult(
                coordinates=z,
                l_drift=l_drift,
                l_virtue=l_virtue,
                quality_flag="nominal",
            )

            # Decode source for critic evaluation
            source = source_bytes_list[i].decode("utf-8", errors="replace")
            critique = critic.evaluate(source, "unknown", projection=projection)
            scores.append(critique.score.value)
        except Exception as exc:
            warnings.warn(
                f"Calibration: skipping vector {i}: {exc}",
                stacklevel=2,
            )

    if len(scores) < MIN_SCORES_FOR_CALIBRATION:
        raise ValueError(
            f"Only {len(scores)} vectors produced valid scores "
            f"(minimum {MIN_SCORES_FOR_CALIBRATION} required for calibration)"
        )

    arr = np.array(scores, dtype=np.float64)
    return ScoreDistribution(
        min=float(np.min(arr)),
        p10=float(np.percentile(arr, 10)),
        p25=float(np.percentile(arr, 25)),
        median=float(np.median(arr)),
        p75=float(np.percentile(arr, 75)),
        p90=float(np.percentile(arr, 90)),
        max=float(np.max(arr)),
        n_scores=len(scores),
    )


def derive_thresholds(distribution: ScoreDistribution) -> CalibrationThresholds:
    """Derive accept/reject thresholds from a score distribution.

    Always uses p25 as accept threshold and p75 as reject threshold.
    Scores below accept → "accept", above reject → "reject", between → "marginal"/"warn".

    Args:
        distribution: Score distribution from compute_score_distribution().

    Returns:
        CalibrationThresholds with accept=p25, reject=p75.

    Raises:
        ValueError: If p25 >= p75 (degenerate distribution, e.g., all scores identical).
    """
    if distribution.p25 >= distribution.p75:
        raise ValueError(
            f"Degenerate score distribution: p25={distribution.p25} >= "
            f"p75={distribution.p75}. Cannot derive meaningful thresholds."
        )

    return CalibrationThresholds(
        accept=distribution.p25,
        reject=distribution.p75,
        source_percentiles=(25.0, 75.0),
        n_scores=distribution.n_scores,
    )

"""Contract tests for 015-threshold-calibration.

Tests backward compatibility with pre-015 models, model threshold round-trip,
and DynamicHelm threshold resolution.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from eigenhelm.models import (
    FEATURE_DIM,
    EigenspaceModel,
    ScoreDistribution,
    TrainingResult,
)


def _make_pre015_model(tmp_path: Path) -> Path:
    """Create a minimal .npz model WITHOUT calibration keys (pre-015 format)."""
    rng = np.random.default_rng(42)
    W = np.linalg.qr(rng.standard_normal((FEATURE_DIM, 3)))[0][:, :3]
    mean = rng.standard_normal(FEATURE_DIM)
    std = np.abs(rng.standard_normal(FEATURE_DIM)) + 0.1

    arrays = {
        "projection_matrix": W,
        "mean": mean,
        "std": std,
        "n_components": np.array(3),
        "version": np.array("pre-015-test"),
        "corpus_hash": np.array("0" * 64),
        "sigma_drift": np.array(1.5),
        "sigma_virtue": np.array(1.2),
        "n_exemplars": np.array(0),
        "n_training_files": np.array(10),
    }
    model_path = tmp_path / "pre015.npz"
    np.savez(model_path, **arrays)
    return model_path


def _make_post015_model(tmp_path: Path) -> Path:
    """Create a .npz model WITH calibration keys (post-015 format)."""
    rng = np.random.default_rng(42)
    W = np.linalg.qr(rng.standard_normal((FEATURE_DIM, 3)))[0][:, :3]
    mean = rng.standard_normal(FEATURE_DIM)
    std = np.abs(rng.standard_normal(FEATURE_DIM)) + 0.1

    arrays = {
        "projection_matrix": W,
        "mean": mean,
        "std": std,
        "n_components": np.array(3),
        "version": np.array("post-015-test"),
        "corpus_hash": np.array("1" * 64),
        "sigma_drift": np.array(1.5),
        "sigma_virtue": np.array(1.2),
        "n_exemplars": np.array(0),
        "n_training_files": np.array(50),
        "calibrated_accept": np.array(0.52, dtype=np.float64),
        "calibrated_reject": np.array(0.72, dtype=np.float64),
        "score_dist_min": np.array(0.38, dtype=np.float64),
        "score_dist_p10": np.array(0.45, dtype=np.float64),
        "score_dist_p25": np.array(0.52, dtype=np.float64),
        "score_dist_median": np.array(0.61, dtype=np.float64),
        "score_dist_p75": np.array(0.72, dtype=np.float64),
        "score_dist_p90": np.array(0.81, dtype=np.float64),
        "score_dist_max": np.array(0.93, dtype=np.float64),
        "score_dist_n_scores": np.array(500),
    }
    model_path = tmp_path / "post015.npz"
    np.savez(model_path, **arrays)
    return model_path


class TestPre015BackwardCompat:
    """T014: Pre-015 models load with None calibration fields, no errors."""

    def test_load_pre015_model_has_none_calibration(self, tmp_path: Path) -> None:
        """load_model on a pre-015 .npz returns None calibration fields."""
        from eigenhelm.eigenspace import load_model

        model_path = _make_pre015_model(tmp_path)
        model = load_model(model_path)

        assert model.calibrated_accept is None
        assert model.calibrated_reject is None
        assert model.score_distribution is None

    def test_load_pre015_model_preserves_existing_fields(self, tmp_path: Path) -> None:
        """Pre-015 model loading preserves sigma_drift, sigma_virtue, etc."""
        from eigenhelm.eigenspace import load_model

        model_path = _make_pre015_model(tmp_path)
        model = load_model(model_path)

        assert model.sigma_drift == pytest.approx(1.5)
        assert model.sigma_virtue == pytest.approx(1.2)
        assert model.version == "pre-015-test"


class TestDynamicHelmThresholdResolution:
    """T015: DynamicHelm uses hardcoded defaults when model has no calibration."""

    def test_pre015_model_uses_hardcoded_defaults(self, tmp_path: Path) -> None:
        """DynamicHelm with pre-015 model falls back to 0.4/0.6."""
        from eigenhelm.eigenspace import load_model
        from eigenhelm.helm import DynamicHelm

        model_path = _make_pre015_model(tmp_path)
        model = load_model(model_path)
        helm = DynamicHelm(eigenspace=model)

        assert helm._accept_threshold == 0.4
        assert helm._reject_threshold == 0.6

    def test_post015_model_uses_calibrated_thresholds(self, tmp_path: Path) -> None:
        """DynamicHelm with post-015 model uses calibrated thresholds."""
        from eigenhelm.eigenspace import load_model
        from eigenhelm.helm import DynamicHelm

        model_path = _make_post015_model(tmp_path)
        model = load_model(model_path)
        helm = DynamicHelm(eigenspace=model)

        assert helm._accept_threshold == pytest.approx(0.52)
        assert helm._reject_threshold == pytest.approx(0.72)

    def test_explicit_thresholds_override_model(self, tmp_path: Path) -> None:
        """Explicit threshold args override model calibration."""
        from eigenhelm.eigenspace import load_model
        from eigenhelm.helm import DynamicHelm

        model_path = _make_post015_model(tmp_path)
        model = load_model(model_path)
        helm = DynamicHelm(
            eigenspace=model,
            accept_threshold=0.3,
            reject_threshold=0.8,
        )

        assert helm._accept_threshold == 0.3
        assert helm._reject_threshold == 0.8

    def test_no_model_uses_hardcoded_defaults(self) -> None:
        """DynamicHelm without eigenspace uses 0.4/0.6."""
        from eigenhelm.helm import DynamicHelm

        helm = DynamicHelm()
        assert helm._accept_threshold == 0.4
        assert helm._reject_threshold == 0.6


class TestModelRoundTrip:
    """T016: Round-trip save/load preserves calibration data exactly."""

    def test_round_trip_preserves_calibration(self, tmp_path: Path) -> None:
        """Save and load a post-015 model; calibration fields match exactly."""
        from eigenhelm.eigenspace import load_model

        model_path = _make_post015_model(tmp_path)
        model = load_model(model_path)

        assert model.calibrated_accept == pytest.approx(0.52)
        assert model.calibrated_reject == pytest.approx(0.72)

    def test_round_trip_preserves_score_distribution(self, tmp_path: Path) -> None:
        """Save and load a post-015 model; score distribution fields match."""
        from eigenhelm.eigenspace import load_model

        model_path = _make_post015_model(tmp_path)
        model = load_model(model_path)

        sd = model.score_distribution
        assert sd is not None
        assert sd.min == pytest.approx(0.38)
        assert sd.p10 == pytest.approx(0.45)
        assert sd.p25 == pytest.approx(0.52)
        assert sd.median == pytest.approx(0.61)
        assert sd.p75 == pytest.approx(0.72)
        assert sd.p90 == pytest.approx(0.81)
        assert sd.max == pytest.approx(0.93)

    def test_training_result_round_trip(self, tmp_path: Path) -> None:
        """Full TrainingResult save/load round-trip preserves calibration."""
        from eigenhelm.training import save_model
        from eigenhelm.eigenspace import load_model

        rng = np.random.default_rng(99)
        W = np.linalg.qr(rng.standard_normal((FEATURE_DIM, 3)))[0][:, :3]
        mean = rng.standard_normal(FEATURE_DIM)
        std = np.abs(rng.standard_normal(FEATURE_DIM)) + 0.1

        score_dist = ScoreDistribution(
            min=0.40, p10=0.46, p25=0.53, median=0.60,
            p75=0.71, p90=0.80, max=0.92, n_scores=200,
        )
        model = EigenspaceModel(
            projection_matrix=W,
            mean=mean,
            std=std,
            n_components=3,
            version="rt-test",
            corpus_hash="a" * 64,
            sigma_drift=1.5,
            sigma_virtue=1.2,
            calibrated_accept=0.53,
            calibrated_reject=0.71,
            score_distribution=score_dist,
        )
        result = TrainingResult(
            model=model,
            explained_variance_ratio=np.array([0.5, 0.3, 0.1]),
            cumulative_variance=0.9,
            n_files_processed=20,
            n_files_skipped=2,
            n_units_extracted=100,
            n_vectors_excluded=0,
            score_distribution=score_dist,
        )

        model_path = tmp_path / "rt.npz"
        save_model(result, model_path)
        loaded = load_model(model_path)

        assert loaded.calibrated_accept == pytest.approx(0.53)
        assert loaded.calibrated_reject == pytest.approx(0.71)
        assert loaded.score_distribution is not None
        assert loaded.score_distribution.p25 == pytest.approx(0.53)
        assert loaded.score_distribution.p75 == pytest.approx(0.71)
        assert loaded.score_distribution.n_scores == 200

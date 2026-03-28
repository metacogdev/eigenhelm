"""Unit tests for calibration: compute_calibration() (006) and threshold calibration (015)."""

from __future__ import annotations

import numpy as np
import pytest
from eigenhelm.training.pca import compute_calibration, compute_pca

from eigenhelm.models import (
    FEATURE_DIM,
    CalibrationStats,
    CalibrationThresholds,
    EigenspaceModel,
    ScoreDistribution,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_design_matrix(
    n: int = 20, seed: int = 0
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return (X, W, mean, std) for a synthetic corpus of n vectors."""
    rng = np.random.default_rng(seed)
    X = rng.standard_normal((n, 69)).astype(np.float64)
    W, mean, std, _ = compute_pca(X, n_components=5)
    return X, W, mean, std


def _make_calibrated_model(
    tmp_path, accept: float = 0.52, reject: float = 0.72
) -> EigenspaceModel:
    """Build an EigenspaceModel with calibration data (post-015)."""
    rng = np.random.default_rng(42)
    W = np.linalg.qr(rng.standard_normal((FEATURE_DIM, 3)))[0][:, :3]
    mean = rng.standard_normal(FEATURE_DIM)
    std = np.abs(rng.standard_normal(FEATURE_DIM)) + 0.1
    return EigenspaceModel(
        projection_matrix=W,
        mean=mean,
        std=std,
        n_components=3,
        version="test-015",
        corpus_hash="a" * 64,
        sigma_drift=1.5,
        sigma_virtue=1.2,
        calibrated_accept=accept,
        calibrated_reject=reject,
        score_distribution=ScoreDistribution(
            min=0.38,
            p10=0.45,
            p25=accept,
            median=0.61,
            p75=reject,
            p90=0.81,
            max=0.93,
            n_scores=100,
        ),
    )


def _make_uncalibrated_model(tmp_path) -> EigenspaceModel:
    """Build an EigenspaceModel without calibration data (pre-015)."""
    rng = np.random.default_rng(42)
    W = np.linalg.qr(rng.standard_normal((FEATURE_DIM, 3)))[0][:, :3]
    mean = rng.standard_normal(FEATURE_DIM)
    std = np.abs(rng.standard_normal(FEATURE_DIM)) + 0.1
    return EigenspaceModel(
        projection_matrix=W,
        mean=mean,
        std=std,
        n_components=3,
        version="test-pre015",
        corpus_hash="b" * 64,
        sigma_drift=1.5,
        sigma_virtue=1.2,
    )


# ---------------------------------------------------------------------------
# (a) Returns CalibrationStats with sigma_drift > 0 and sigma_virtue > 0
# ---------------------------------------------------------------------------


class TestBasicReturn:
    def test_returns_calibration_stats(self):
        X, W, mean, std = _make_design_matrix()
        result = compute_calibration(X, W, mean, std)
        assert isinstance(result, CalibrationStats)

    def test_sigma_drift_positive(self):
        X, W, mean, std = _make_design_matrix()
        result = compute_calibration(X, W, mean, std)
        assert result.sigma_drift > 0.0

    def test_sigma_virtue_positive(self):
        X, W, mean, std = _make_design_matrix()
        result = compute_calibration(X, W, mean, std)
        assert result.sigma_virtue > 0.0


# ---------------------------------------------------------------------------
# (b) n_projections == N
# ---------------------------------------------------------------------------


class TestNProjections:
    def test_n_projections_equals_n(self):
        X, W, mean, std = _make_design_matrix(n=30)
        result = compute_calibration(X, W, mean, std)
        assert result.n_projections == 30

    def test_n_projections_single_row(self):
        X, W, mean, std = _make_design_matrix(n=10)
        single = X[:1]
        result = compute_calibration(single, W, mean, std)
        assert result.n_projections == 1


# ---------------------------------------------------------------------------
# (c) percentile stored as provided
# ---------------------------------------------------------------------------


class TestPercentileStored:
    def test_default_percentile_is_95(self):
        X, W, mean, std = _make_design_matrix()
        result = compute_calibration(X, W, mean, std)
        assert result.percentile == 95.0

    def test_custom_percentile_stored(self):
        X, W, mean, std = _make_design_matrix()
        result = compute_calibration(X, W, mean, std, percentile=50.0)
        assert result.percentile == 50.0

    def test_higher_percentile_geq_lower_percentile(self):
        X, W, mean, std = _make_design_matrix(n=50)
        r50 = compute_calibration(X, W, mean, std, percentile=50.0)
        r95 = compute_calibration(X, W, mean, std, percentile=95.0)
        assert r95.sigma_drift >= r50.sigma_drift
        assert r95.sigma_virtue >= r50.sigma_virtue


# ---------------------------------------------------------------------------
# (d) N=1 edge case — sigma equals the single observation's l_drift / l_virtue
# ---------------------------------------------------------------------------


class TestSingleRowEdgeCase:
    def test_n1_sigma_drift_matches_single_observation(self):
        X, W, mean, std = _make_design_matrix(n=10)
        single = X[:1]
        result = compute_calibration(single, W, mean, std)
        # Manually compute expected values
        X_std = (single - mean) / std
        Z = X_std @ W
        X_rec = Z @ W.T
        expected_drift = float(np.linalg.norm(X_rec - X_std, axis=1)[0])
        expected_virtue = float(np.linalg.norm(Z, axis=1)[0])
        assert abs(result.sigma_drift - max(expected_drift, 1e-8)) < 1e-9
        assert abs(result.sigma_virtue - max(expected_virtue, 1e-8)) < 1e-9


# ---------------------------------------------------------------------------
# (e) All-zero / degenerate rows — floor prevents zero sigma and ValueError
# ---------------------------------------------------------------------------


class TestDegenerateCorpus:
    def test_all_zero_rows_no_value_error(self):
        """All-zero design matrix must not raise ValueError from CalibrationStats."""
        X, W, mean, std = _make_design_matrix(n=10)
        zero_X = np.zeros((5, 69), dtype=np.float64)
        # Should not raise
        result = compute_calibration(zero_X, W, mean, std)
        assert result.sigma_drift > 0.0
        assert result.sigma_virtue > 0.0

    def test_mean_identical_rows_sigma_equals_floor(self):
        """Rows equal to the corpus mean → X_std=0 → Z=0 → l_virtue=0 → floor applies."""
        X, W, mean, std = _make_design_matrix(n=10)
        # All rows = mean → (X - mean)/std = 0 → Z = 0, X_rec = 0 → both norms = 0
        mean_X = np.tile(mean, (5, 1))
        result = compute_calibration(mean_X, W, mean, std)
        assert result.sigma_drift == pytest.approx(1e-8)
        assert result.sigma_virtue == pytest.approx(1e-8)

    def test_identical_rows_no_zero_sigma(self):
        """Corpus of identical vectors must not produce sigma=0."""
        X, W, mean, std = _make_design_matrix(n=10)
        # All rows identical — percentile of identical values = that value
        repeated = np.tile(X[0], (10, 1))
        result = compute_calibration(repeated, W, mean, std)
        assert result.sigma_drift > 0.0
        assert result.sigma_virtue > 0.0


# ---------------------------------------------------------------------------
# 015 Threshold Calibration — ScoreDistribution validation
# ---------------------------------------------------------------------------


class TestScoreDistribution:
    def test_valid_construction(self):
        sd = ScoreDistribution(
            min=0.1,
            p10=0.2,
            p25=0.3,
            median=0.5,
            p75=0.7,
            p90=0.8,
            max=0.9,
            n_scores=100,
        )
        assert sd.min == 0.1
        assert sd.n_scores == 100

    def test_all_same_values(self):
        sd = ScoreDistribution(
            min=0.5,
            p10=0.5,
            p25=0.5,
            median=0.5,
            p75=0.5,
            p90=0.5,
            max=0.5,
            n_scores=10,
        )
        assert sd.median == 0.5

    def test_boundary_values(self):
        sd = ScoreDistribution(
            min=0.0,
            p10=0.0,
            p25=0.0,
            median=0.5,
            p75=1.0,
            p90=1.0,
            max=1.0,
            n_scores=1,
        )
        assert sd.min == 0.0
        assert sd.max == 1.0

    def test_out_of_range_raises(self):
        with pytest.raises(ValueError, match=r"must be in \[0\.0, 1\.0\]"):
            ScoreDistribution(
                min=-0.1,
                p10=0.2,
                p25=0.3,
                median=0.5,
                p75=0.7,
                p90=0.8,
                max=0.9,
                n_scores=10,
            )

    def test_non_monotonic_raises(self):
        with pytest.raises(ValueError, match="monoton"):
            ScoreDistribution(
                min=0.5,
                p10=0.2,
                p25=0.3,
                median=0.5,
                p75=0.7,
                p90=0.8,
                max=0.9,
                n_scores=10,
            )

    def test_frozen(self):
        sd = ScoreDistribution(
            min=0.1,
            p10=0.2,
            p25=0.3,
            median=0.5,
            p75=0.7,
            p90=0.8,
            max=0.9,
            n_scores=50,
        )
        with pytest.raises(AttributeError):
            sd.min = 0.0  # type: ignore[misc]


# ---------------------------------------------------------------------------
# 015 Threshold Calibration — CalibrationThresholds validation
# ---------------------------------------------------------------------------


class TestCalibrationThresholds:
    def test_valid_construction(self):
        ct = CalibrationThresholds(
            accept=0.3,
            reject=0.7,
            source_percentiles=(25.0, 75.0),
            n_scores=100,
        )
        assert ct.accept == 0.3
        assert ct.reject == 0.7

    def test_accept_equals_reject_raises(self):
        with pytest.raises(ValueError):
            CalibrationThresholds(
                accept=0.5,
                reject=0.5,
                source_percentiles=(25.0, 75.0),
                n_scores=100,
            )

    def test_accept_greater_than_reject_raises(self):
        with pytest.raises(ValueError):
            CalibrationThresholds(
                accept=0.8,
                reject=0.3,
                source_percentiles=(25.0, 75.0),
                n_scores=100,
            )

    def test_out_of_range_raises(self):
        with pytest.raises(ValueError):
            CalibrationThresholds(
                accept=-0.1,
                reject=0.7,
                source_percentiles=(25.0, 75.0),
                n_scores=100,
            )

    def test_frozen(self):
        ct = CalibrationThresholds(
            accept=0.3,
            reject=0.7,
            source_percentiles=(25.0, 75.0),
            n_scores=50,
        )
        with pytest.raises(AttributeError):
            ct.accept = 0.1  # type: ignore[misc]


# ---------------------------------------------------------------------------
# 015 Threshold Calibration — derive_thresholds()
# ---------------------------------------------------------------------------


class TestDeriveThresholds:
    def test_normal_case(self):
        from eigenhelm.training.calibration import derive_thresholds

        dist = ScoreDistribution(
            min=0.1,
            p10=0.2,
            p25=0.35,
            median=0.5,
            p75=0.72,
            p90=0.85,
            max=0.95,
            n_scores=100,
        )
        thresholds = derive_thresholds(dist)
        assert thresholds.accept == pytest.approx(0.35)
        assert thresholds.reject == pytest.approx(0.72)
        assert thresholds.source_percentiles == (25.0, 75.0)
        assert thresholds.n_scores == 100

    def test_degenerate_distribution_raises(self):
        from eigenhelm.training.calibration import derive_thresholds

        dist = ScoreDistribution(
            min=0.5,
            p10=0.5,
            p25=0.5,
            median=0.5,
            p75=0.5,
            p90=0.5,
            max=0.5,
            n_scores=20,
        )
        with pytest.raises(ValueError, match="Degenerate"):
            derive_thresholds(dist)


# ---------------------------------------------------------------------------
# 015 Threshold Calibration — Threshold hierarchy (T019)
# ---------------------------------------------------------------------------


class TestThresholdHierarchy:
    """Test the 4-level threshold resolution: hardcoded < model < config < CLI."""

    def test_no_model_no_args_uses_hardcoded(self):
        """No model, no explicit args → hardcoded 0.4/0.6."""
        from eigenhelm.helm import DynamicHelm

        helm = DynamicHelm()
        assert helm._accept_threshold == 0.4
        assert helm._reject_threshold == 0.6

    def test_model_calibration_overrides_hardcoded(self, tmp_path):
        """Post-015 model overrides hardcoded defaults."""
        from eigenhelm.helm import DynamicHelm

        model = _make_calibrated_model(tmp_path, accept=0.52, reject=0.72)
        helm = DynamicHelm(eigenspace=model)
        assert helm._accept_threshold == pytest.approx(0.52)
        assert helm._reject_threshold == pytest.approx(0.72)

    def test_explicit_args_override_model(self, tmp_path):
        """Explicit threshold args override model calibration."""
        from eigenhelm.helm import DynamicHelm

        model = _make_calibrated_model(tmp_path, accept=0.52, reject=0.72)
        helm = DynamicHelm(
            eigenspace=model,
            accept_threshold=0.3,
            reject_threshold=0.8,
        )
        assert helm._accept_threshold == 0.3
        assert helm._reject_threshold == 0.8

    def test_partial_override_accept_only(self, tmp_path):
        """CLI sets accept only; reject comes from model."""
        from eigenhelm.helm import DynamicHelm

        model = _make_calibrated_model(tmp_path, accept=0.52, reject=0.72)
        helm = DynamicHelm(eigenspace=model, accept_threshold=0.2)
        assert helm._accept_threshold == 0.2
        assert helm._reject_threshold == pytest.approx(0.72)

    def test_partial_override_reject_only(self, tmp_path):
        """CLI sets reject only; accept comes from model."""
        from eigenhelm.helm import DynamicHelm

        model = _make_calibrated_model(tmp_path, accept=0.52, reject=0.72)
        helm = DynamicHelm(eigenspace=model, reject_threshold=0.9)
        assert helm._accept_threshold == pytest.approx(0.52)
        assert helm._reject_threshold == 0.9

    def test_no_calibration_falls_to_hardcoded(self, tmp_path):
        """Pre-015 model without calibration → hardcoded 0.4/0.6."""
        from eigenhelm.helm import DynamicHelm

        model = _make_uncalibrated_model(tmp_path)
        helm = DynamicHelm(eigenspace=model)
        assert helm._accept_threshold == 0.4
        assert helm._reject_threshold == 0.6


# ---------------------------------------------------------------------------
# 015 Threshold Calibration — compute_score_distribution() (T022)
# ---------------------------------------------------------------------------


def _build_scoring_model(n_train: int = 30, seed: int = 0) -> tuple:
    """Build a minimal EigenspaceModel + design matrix + source bytes for scoring tests.

    Returns (model, X, source_bytes_list) where model has valid sigma values.
    """
    from eigenhelm.training.pca import compute_pca

    rng = np.random.default_rng(seed)
    X = rng.standard_normal((n_train, FEATURE_DIM)).astype(np.float64)
    W, mean, std, _ = compute_pca(X, n_components=5)

    model = EigenspaceModel(
        projection_matrix=W,
        mean=mean,
        std=std,
        n_components=5,
        version="test-scoring",
        corpus_hash="c" * 64,
        sigma_drift=1.5,
        sigma_virtue=1.2,
    )

    # Simple Python source bytes for each vector
    source_bytes = [f"def f{i}(): return {i}".encode() for i in range(n_train)]
    return model, X, source_bytes


class TestComputeScoreDistribution:
    """Tests for compute_score_distribution() — T022."""

    def test_returns_score_distribution(self):
        """Basic call returns ScoreDistribution with valid fields."""
        from eigenhelm.training.calibration import compute_score_distribution

        model, X, src = _build_scoring_model(n_train=15)
        dist = compute_score_distribution(X, model, src)
        assert isinstance(dist, ScoreDistribution)
        assert dist.n_scores == 15
        assert 0.0 <= dist.min <= dist.max <= 1.0

    def test_too_few_vectors_raises(self):
        """Fewer than MIN_SCORES_FOR_CALIBRATION vectors → ValueError (FR-009)."""
        from eigenhelm.training.calibration import compute_score_distribution

        model, X, src = _build_scoring_model(n_train=15)
        # Pass only 5 vectors (below minimum of 10)
        with pytest.raises(ValueError, match="minimum"):
            compute_score_distribution(X[:5], model, src[:5])

    def test_determinism(self):
        """Same inputs → same outputs (FR-010)."""
        from eigenhelm.training.calibration import compute_score_distribution

        model, X, src = _build_scoring_model(n_train=15)
        d1 = compute_score_distribution(X, model, src)
        d2 = compute_score_distribution(X, model, src)
        assert d1.min == d2.min
        assert d1.median == d2.median
        assert d1.max == d2.max
        assert d1.n_scores == d2.n_scores

    def test_percentile_ordering(self):
        """Percentiles are monotonically non-decreasing."""
        from eigenhelm.training.calibration import compute_score_distribution

        model, X, src = _build_scoring_model(n_train=20)
        dist = compute_score_distribution(X, model, src)
        assert dist.min <= dist.p10 <= dist.p25 <= dist.median
        assert dist.median <= dist.p75 <= dist.p90 <= dist.max

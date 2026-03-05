"""Unit tests for compute_calibration() in training/pca.py."""

from __future__ import annotations

import numpy as np
import pytest
from eigenhelm.training.pca import compute_calibration, compute_pca

from eigenhelm.models import CalibrationStats

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

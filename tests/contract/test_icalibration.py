"""Contract tests for the calibration API (006-norm-calibration).

Covers:
  (a) train_eigenspace() returns CalibrationStats in TrainingResult.calibration
  (b) result.model.sigma_drift == result.calibration.sigma_drift
  (c) result.model.sigma_virtue == result.calibration.sigma_virtue
  (d) save_model() writes exactly 9 keys; original 7 keys unchanged
  (e) inspect_model() dict contains sigma_drift and sigma_virtue keys
  US3: load_model() emits exactly one warning for pre-calibration models; falls back correctly
"""

from __future__ import annotations

import warnings

import numpy as np
import pytest
from eigenhelm.eigenspace import load_model
from eigenhelm.training import inspect_model, save_model, train_eigenspace

from eigenhelm.models import CalibrationStats

# ---------------------------------------------------------------------------
# (a) train_eigenspace returns CalibrationStats
# ---------------------------------------------------------------------------


@pytest.mark.contract
class TestTrainReturnsCalibration:
    def test_calibration_is_not_none(self, corpus_dir):
        result = train_eigenspace(corpus_dir)
        assert result.calibration is not None

    def test_calibration_is_calibration_stats_instance(self, corpus_dir):
        result = train_eigenspace(corpus_dir)
        assert isinstance(result.calibration, CalibrationStats)

    def test_calibration_n_projections_positive(self, corpus_dir):
        result = train_eigenspace(corpus_dir)
        assert result.calibration.n_projections > 0

    def test_calibration_sigma_drift_positive(self, corpus_dir):
        result = train_eigenspace(corpus_dir)
        assert result.calibration.sigma_drift > 0.0

    def test_calibration_sigma_virtue_positive(self, corpus_dir):
        result = train_eigenspace(corpus_dir)
        assert result.calibration.sigma_virtue > 0.0


# ---------------------------------------------------------------------------
# (b) result.model.sigma_drift == result.calibration.sigma_drift
# ---------------------------------------------------------------------------


@pytest.mark.contract
class TestModelSigmaMatchesCalibration:
    def test_model_sigma_drift_equals_calibration(self, corpus_dir):
        result = train_eigenspace(corpus_dir)
        assert result.model.sigma_drift == result.calibration.sigma_drift

    def test_model_sigma_virtue_equals_calibration(self, corpus_dir):
        result = train_eigenspace(corpus_dir)
        assert result.model.sigma_virtue == result.calibration.sigma_virtue

    def test_sigma_drift_is_not_default_one(self, corpus_dir):
        """A real corpus produces a non-unit sigma_drift."""
        result = train_eigenspace(corpus_dir)
        assert result.model.sigma_drift != pytest.approx(1.0)

    def test_sigma_virtue_is_not_default_one(self, corpus_dir):
        """A real corpus produces a non-unit sigma_virtue."""
        result = train_eigenspace(corpus_dir)
        assert result.model.sigma_virtue != pytest.approx(1.0)


# ---------------------------------------------------------------------------
# (d) save_model writes exactly 9 keys; original 7 unchanged
# ---------------------------------------------------------------------------


@pytest.mark.contract
class TestSaveModelKeys:
    _ORIGINAL_KEYS = frozenset(
        {
            "projection_matrix",
            "mean",
            "std",
            "n_components",
            "version",
            "corpus_hash",
            "explained_variance_ratio",
        }
    )

    def test_nine_keys_written(self, corpus_dir, tmp_path):
        result = train_eigenspace(corpus_dir)
        path = tmp_path / "model.npz"
        save_model(result, path)
        data = np.load(path, allow_pickle=False)
        # 9 original + up to 5 exemplar keys (n_exemplars always present)
        assert len(data.files) >= 10  # at least 9 original + n_exemplars

    def test_new_calibration_keys_present(self, corpus_dir, tmp_path):
        result = train_eigenspace(corpus_dir)
        path = tmp_path / "model.npz"
        save_model(result, path)
        data = np.load(path, allow_pickle=False)
        assert "sigma_drift" in data.files
        assert "sigma_virtue" in data.files

    def test_original_seven_keys_unchanged(self, corpus_dir, tmp_path):
        """FR-009/SC-004: all 7 original keys present and unaffected by new keys."""
        result = train_eigenspace(corpus_dir)
        path = tmp_path / "model.npz"
        save_model(result, path)
        data = np.load(path, allow_pickle=False)
        assert self._ORIGINAL_KEYS.issubset(set(data.files))
        # Spot-check: n_components type and value preserved
        assert int(data["n_components"]) == result.model.n_components

    def test_sigma_values_are_scalar_float64(self, corpus_dir, tmp_path):
        result = train_eigenspace(corpus_dir)
        path = tmp_path / "model.npz"
        save_model(result, path)
        data = np.load(path, allow_pickle=False)
        assert data["sigma_drift"].dtype == np.float64
        assert data["sigma_virtue"].dtype == np.float64
        assert data["sigma_drift"].shape == ()
        assert data["sigma_virtue"].shape == ()


# ---------------------------------------------------------------------------
# (e) inspect_model dict contains sigma_drift and sigma_virtue
# ---------------------------------------------------------------------------


@pytest.mark.contract
class TestInspectModelSigmaKeys:
    def test_sigma_drift_in_inspect_dict(self, corpus_dir, tmp_path):
        result = train_eigenspace(corpus_dir)
        path = tmp_path / "model.npz"
        save_model(result, path)
        info = inspect_model(path)
        assert "sigma_drift" in info

    def test_sigma_virtue_in_inspect_dict(self, corpus_dir, tmp_path):
        result = train_eigenspace(corpus_dir)
        path = tmp_path / "model.npz"
        save_model(result, path)
        info = inspect_model(path)
        assert "sigma_virtue" in info

    def test_sigma_values_match_model(self, corpus_dir, tmp_path):
        result = train_eigenspace(corpus_dir)
        path = tmp_path / "model.npz"
        save_model(result, path)
        info = inspect_model(path)
        assert info["sigma_drift"] == pytest.approx(result.model.sigma_drift)
        assert info["sigma_virtue"] == pytest.approx(result.model.sigma_virtue)

    def test_sigma_none_for_old_model(self, tmp_path):
        """Models without sigma keys → inspect returns None for both."""
        # Create a minimal 7-key npz (simulating pre-calibration model)
        import numpy as np
        from eigenhelm.eigenspace import make_synthetic_model

        model = make_synthetic_model()
        np.savez(
            tmp_path / "old.npz",
            projection_matrix=model.projection_matrix,
            mean=model.mean,
            std=model.std,
            n_components=np.array(model.n_components),
            version=np.array(model.version),
            corpus_hash=np.array(model.corpus_hash),
            explained_variance_ratio=np.ones(model.n_components) / model.n_components,
        )
        info = inspect_model(tmp_path / "old.npz")
        assert info["sigma_drift"] is None
        assert info["sigma_virtue"] is None


# ---------------------------------------------------------------------------
# US3: backwards-compatibility — load_model on pre-calibration models
# ---------------------------------------------------------------------------


@pytest.mark.contract
class TestLoadModelBackwardsCompat:
    @pytest.fixture
    def pre_calibration_model_path(self, tmp_path):
        """Create a synthetic pre-calibration .npz (no sigma keys)."""
        import numpy as np

        n_features = 69
        n_components = 5
        path = tmp_path / "pre_calibration.npz"
        rng = np.random.default_rng(42)
        np.savez(
            path,
            projection_matrix=rng.standard_normal((n_features, n_components)),
            mean=np.zeros(n_features),
            std=np.ones(n_features),
            explained_variance_ratio=np.full(n_components, 1.0 / n_components),
            n_components=np.array(n_components),
            version="0.1.0",
            corpus_hash="abc123",
        )
        return path

    def test_load_old_model_no_exception(self, pre_calibration_model_path):
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            model = load_model(pre_calibration_model_path)
        assert model is not None

    def test_load_old_model_emits_exactly_one_warning(self, pre_calibration_model_path):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            load_model(pre_calibration_model_path)
        assert len(caught) == 1

    def test_load_old_model_warning_mentions_calibration(
        self, pre_calibration_model_path
    ):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            load_model(pre_calibration_model_path)
        assert "calibration" in str(caught[0].message).lower()

    def test_load_old_model_warning_mentions_path(self, pre_calibration_model_path):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            load_model(pre_calibration_model_path)
        assert "pre_calibration.npz" in str(caught[0].message)

    def test_load_old_model_sigma_defaults_to_one(self, pre_calibration_model_path):
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            model = load_model(pre_calibration_model_path)
        assert model.sigma_drift == 1.0
        assert model.sigma_virtue == 1.0

    def test_load_new_model_no_warning(self, corpus_dir, tmp_path):
        """A freshly trained and saved model loads without any warning."""
        result = train_eigenspace(corpus_dir)
        path = tmp_path / "calibrated.npz"
        save_model(result, path)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            model = load_model(path)
        cal_warnings = [w for w in caught if "calibration" in str(w.message).lower()]
        assert cal_warnings == []
        assert model.sigma_drift == pytest.approx(result.model.sigma_drift)
        assert model.sigma_virtue == pytest.approx(result.model.sigma_virtue)

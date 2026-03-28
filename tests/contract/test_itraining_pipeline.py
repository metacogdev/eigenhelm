"""Contract tests for the training pipeline public API.

Tests are written FIRST (TDD) and must FAIL before implementation.
These tests cover:
  - T027: train_eigenspace() contract
  - T028: save_model() contract
  - T030: inspect_model() contract
"""

from __future__ import annotations

import numpy as np
import pytest
from eigenhelm.training import inspect_model, save_model, train_eigenspace

from eigenhelm.models import TrainingResult

# ---------------------------------------------------------------------------
# T027: train_eigenspace() contract
# ---------------------------------------------------------------------------


@pytest.mark.contract
class TestTrainEigenspaceContract:
    def test_valid_corpus_returns_training_result(self, corpus_dir):
        """train_eigenspace() on a valid corpus returns a TrainingResult."""
        result = train_eigenspace(corpus_dir)
        assert isinstance(result, TrainingResult)

    def test_result_has_model(self, corpus_dir):
        """TrainingResult.model is an EigenspaceModel."""
        from eigenhelm.models import EigenspaceModel

        result = train_eigenspace(corpus_dir)
        assert isinstance(result.model, EigenspaceModel)

    def test_projection_matrix_shape(self, corpus_dir):
        """projection_matrix.shape[0] == 69."""
        result = train_eigenspace(corpus_dir)
        assert result.model.projection_matrix.shape[0] == 69

    def test_projection_matrix_n_components_consistent(self, corpus_dir):
        """projection_matrix.shape[1] == model.n_components."""
        result = train_eigenspace(corpus_dir)
        assert result.model.projection_matrix.shape[1] == result.model.n_components

    def test_explained_variance_ratio_shape(self, corpus_dir):
        """explained_variance_ratio has shape (k,)."""
        result = train_eigenspace(corpus_dir)
        k = result.model.n_components
        assert result.explained_variance_ratio.shape == (k,)

    def test_explained_variance_ratio_sums_to_cumulative(self, corpus_dir):
        """explained_variance_ratio.sum() ≈ cumulative_variance."""
        result = train_eigenspace(corpus_dir)
        assert (
            abs(result.explained_variance_ratio.sum() - result.cumulative_variance)
            < 1e-9
        )

    def test_cumulative_variance_meets_threshold(self, corpus_dir):
        """Auto-selected components meet the default 90% threshold."""
        result = train_eigenspace(corpus_dir, variance_threshold=0.90)
        assert result.cumulative_variance >= 0.90

    def test_corpus_hash_is_64_char_hex(self, corpus_dir):
        """corpus_hash is a 64-character hex string."""
        result = train_eigenspace(corpus_dir)
        h = result.model.corpus_hash
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_n_files_processed_positive(self, corpus_dir):
        """n_files_processed > 0 for a non-empty corpus."""
        result = train_eigenspace(corpus_dir)
        assert result.n_files_processed > 0

    def test_n_units_extracted_positive(self, corpus_dir):
        """n_units_extracted > 0 — corpus must yield code units."""
        result = train_eigenspace(corpus_dir)
        assert result.n_units_extracted > 0

    def test_missing_corpus_raises_file_not_found(self, tmp_path):
        """train_eigenspace() raises FileNotFoundError for missing corpus_dir."""
        with pytest.raises(FileNotFoundError):
            train_eigenspace(tmp_path / "nonexistent")

    def test_empty_corpus_raises_value_error(self, tmp_path):
        """train_eigenspace() raises ValueError for a corpus with no eligible files."""
        # Create a dir with only non-source files
        (tmp_path / "README.md").write_text("hello")
        with pytest.raises(ValueError, match="[Nn]o eligible"):
            train_eigenspace(tmp_path)

    def test_version_defaults_to_package_version(self, corpus_dir):
        """version defaults to the installed package version."""
        from eigenhelm.training import get_package_version

        result = train_eigenspace(corpus_dir)
        assert result.model.version == get_package_version()

    def test_explicit_version_propagates(self, corpus_dir):
        """Explicit version string propagates to model.version."""
        result = train_eigenspace(corpus_dir, version="test-1.0")
        assert result.model.version == "test-1.0"

    def test_explicit_n_components_respected(self, corpus_dir):
        """Explicit n_components produces model with that many components."""
        result = train_eigenspace(corpus_dir, n_components=2)
        assert result.model.n_components == 2
        assert result.model.projection_matrix.shape == (69, 2)

    def test_mean_shape(self, corpus_dir):
        """model.mean has shape (69,)."""
        result = train_eigenspace(corpus_dir)
        assert result.model.mean.shape == (69,)

    def test_std_positive(self, corpus_dir):
        """model.std > 0 for all dimensions."""
        result = train_eigenspace(corpus_dir)
        assert np.all(result.model.std > 0)


# ---------------------------------------------------------------------------
# T028: save_model() contract
# ---------------------------------------------------------------------------


@pytest.mark.contract
class TestSaveModelContract:
    def test_save_writes_loadable_npz(self, corpus_dir, tmp_path):
        """save_model() writes a .npz file with all 7 required keys."""
        result = train_eigenspace(corpus_dir)
        path = tmp_path / "model.npz"
        save_model(result, path)
        assert path.exists()
        data = np.load(path, allow_pickle=True)
        expected_keys = {
            "projection_matrix",
            "mean",
            "std",
            "n_components",
            "version",
            "corpus_hash",
            "explained_variance_ratio",
        }
        assert expected_keys.issubset(set(data.files))

    def test_save_projection_matrix_correct(self, corpus_dir, tmp_path):
        """Saved projection_matrix matches TrainingResult.model.projection_matrix."""
        result = train_eigenspace(corpus_dir)
        path = tmp_path / "model.npz"
        save_model(result, path)
        data = np.load(path)
        np.testing.assert_array_equal(
            data["projection_matrix"], result.model.projection_matrix
        )

    def test_save_raises_file_exists_error_no_force(self, corpus_dir, tmp_path):
        """save_model() raises FileExistsError when path exists and force=False."""
        result = train_eigenspace(corpus_dir)
        path = tmp_path / "model.npz"
        path.touch()
        with pytest.raises(FileExistsError):
            save_model(result, path, force=False)

    def test_save_force_overwrites_existing(self, corpus_dir, tmp_path):
        """save_model(force=True) overwrites an existing file without error."""
        result = train_eigenspace(corpus_dir)
        path = tmp_path / "model.npz"
        save_model(result, path)
        save_model(result, path, force=True)  # Should not raise
        assert path.exists()

    def test_saved_model_loadable_by_load_model(self, corpus_dir, tmp_path):
        """Model saved by save_model() is loadable by eigenhelm.eigenspace.load_model()."""
        from eigenhelm.eigenspace import load_model

        result = train_eigenspace(corpus_dir)
        path = tmp_path / "model.npz"
        save_model(result, path)
        loaded = load_model(path)
        assert loaded.n_components == result.model.n_components
        np.testing.assert_array_equal(
            loaded.projection_matrix, result.model.projection_matrix
        )


# ---------------------------------------------------------------------------
# T030: inspect_model() contract
# ---------------------------------------------------------------------------


@pytest.mark.contract
class TestInspectModelContract:
    def test_inspect_returns_dict_with_expected_keys(self, corpus_dir, tmp_path):
        """inspect_model() returns dict with all required keys."""
        result = train_eigenspace(corpus_dir)
        path = tmp_path / "model.npz"
        save_model(result, path)
        info = inspect_model(path)
        expected_keys = {
            "n_components",
            "explained_variance_ratio",
            "cumulative_variance",
            "corpus_hash",
            "version",
            "mean_range",
            "std_range",
            "projection_shape",
        }
        assert expected_keys.issubset(set(info.keys()))

    def test_inspect_n_components_correct(self, corpus_dir, tmp_path):
        """inspect_model().n_components matches trained model."""
        result = train_eigenspace(corpus_dir)
        path = tmp_path / "model.npz"
        save_model(result, path)
        info = inspect_model(path)
        assert info["n_components"] == result.model.n_components

    def test_inspect_projection_shape_correct(self, corpus_dir, tmp_path):
        """inspect_model().projection_shape is (69, k)."""
        result = train_eigenspace(corpus_dir)
        path = tmp_path / "model.npz"
        save_model(result, path)
        info = inspect_model(path)
        assert info["projection_shape"] == (69, result.model.n_components)

    def test_inspect_corpus_hash_matches(self, corpus_dir, tmp_path):
        """inspect_model().corpus_hash matches training corpus hash."""
        result = train_eigenspace(corpus_dir)
        path = tmp_path / "model.npz"
        save_model(result, path)
        info = inspect_model(path)
        assert info["corpus_hash"] == result.model.corpus_hash

    def test_inspect_handles_missing_explained_variance_gracefully(self, tmp_path):
        """inspect_model() handles .npz missing explained_variance_ratio key."""
        from eigenhelm.eigenspace import make_synthetic_model

        model = make_synthetic_model(n_components=3, seed=42)
        # Write .npz without explained_variance_ratio (simulating old-format file)
        path = tmp_path / "old_model.npz"
        np.savez(
            path,
            projection_matrix=model.projection_matrix,
            mean=model.mean,
            std=model.std,
            n_components=np.array(model.n_components),
            version=np.array(model.version),
            corpus_hash=np.array(model.corpus_hash),
        )
        info = inspect_model(path)
        # Should not raise; explained_variance_ratio may be None or empty
        assert "n_components" in info

    def test_inspect_raises_key_error_on_malformed_file(self, tmp_path):
        """inspect_model() raises KeyError on a .npz with required keys missing."""
        path = tmp_path / "bad.npz"
        np.savez(path, garbage=np.array([1, 2, 3]))
        with pytest.raises(KeyError):
            inspect_model(path)

    def test_inspect_raises_file_not_found_for_missing_path(self, tmp_path):
        """inspect_model() raises FileNotFoundError for a non-existent path."""
        with pytest.raises(FileNotFoundError):
            inspect_model(tmp_path / "nonexistent.npz")

"""Unit tests for model metadata round-trip (009-model-fleet T011)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from eigenhelm.eigenspace import load_model
from eigenhelm.models import FEATURE_DIM, EigenspaceModel, TrainingResult
from eigenhelm.training.serialization import save_model


def _make_result(
    language: str | None = None,
    corpus_class: str | None = None,
    n_training_files: int = 42,
) -> TrainingResult:
    """Create a minimal TrainingResult with configurable metadata."""
    rng = np.random.default_rng(99)
    W = np.eye(FEATURE_DIM, 3, dtype=np.float64)
    mean = rng.standard_normal(FEATURE_DIM).astype(np.float64)
    std = np.abs(rng.standard_normal(FEATURE_DIM).astype(np.float64)) + 0.1

    model = EigenspaceModel(
        projection_matrix=W,
        mean=mean,
        std=std,
        n_components=3,
        version="test-009",
        corpus_hash="a" * 64,
        sigma_drift=1.5,
        sigma_virtue=2.0,
        language=language,
        corpus_class=corpus_class,
        n_training_files=n_training_files,
    )
    evr = np.array([0.5, 0.3, 0.1], dtype=np.float64)
    return TrainingResult(
        model=model,
        explained_variance_ratio=evr,
        cumulative_variance=0.9,
        n_files_processed=n_training_files,
        n_files_skipped=0,
        n_units_extracted=100,
        n_vectors_excluded=0,
    )


class TestMetadataRoundTrip:
    """Save → load round-trip preserves language metadata."""

    def test_language_and_corpus_class_round_trip(self, tmp_path: Path) -> None:
        result = _make_result(
            language="javascript", corpus_class="A", n_training_files=250
        )
        out = tmp_path / "model.npz"
        save_model(result, out)

        loaded = load_model(out)
        assert loaded.language == "javascript"
        assert loaded.corpus_class == "A"
        assert loaded.n_training_files == 250

    def test_multi_language_class_b(self, tmp_path: Path) -> None:
        result = _make_result(language="multi", corpus_class="B", n_training_files=500)
        out = tmp_path / "model.npz"
        save_model(result, out)

        loaded = load_model(out)
        assert loaded.language == "multi"
        assert loaded.corpus_class == "B"
        assert loaded.n_training_files == 500

    def test_n_training_files_always_persisted(self, tmp_path: Path) -> None:
        """n_training_files is written even when language is None."""
        result = _make_result(language=None, corpus_class=None, n_training_files=77)
        out = tmp_path / "model.npz"
        save_model(result, out)

        data = np.load(out)
        assert "n_training_files" in data.files
        assert int(data["n_training_files"]) == 77

    def test_language_none_skips_language_keys(self, tmp_path: Path) -> None:
        """When language is None, language and corpus_class keys are not written."""
        result = _make_result(language=None, corpus_class=None)
        out = tmp_path / "model.npz"
        save_model(result, out)

        data = np.load(out)
        assert "language" not in data.files
        assert "corpus_class" not in data.files


class TestBackwardCompat:
    """Pre-009 models without metadata load gracefully."""

    def test_pre_009_model_loads_with_none_defaults(self, tmp_path: Path) -> None:
        """A .npz file without language/corpus_class/n_training_files keys loads OK."""
        rng = np.random.default_rng(42)
        W = np.eye(FEATURE_DIM, 3, dtype=np.float64)
        mean = rng.standard_normal(FEATURE_DIM).astype(np.float64)
        std = np.abs(rng.standard_normal(FEATURE_DIM).astype(np.float64)) + 0.1

        out = tmp_path / "old_model.npz"
        np.savez(
            out,
            projection_matrix=W,
            mean=mean,
            std=std,
            n_components=np.array(3),
            version=np.array("0.1.0"),
            corpus_hash=np.array("b" * 64),
            sigma_drift=np.array(1.0),
            sigma_virtue=np.array(1.0),
            n_exemplars=np.array(0),
        )

        loaded = load_model(out)
        assert loaded.language is None
        assert loaded.corpus_class is None
        assert loaded.n_training_files == 0

    def test_existing_fields_unaffected(self, tmp_path: Path) -> None:
        """Adding metadata doesn't change existing model fields."""
        result = _make_result(language="go", corpus_class="A", n_training_files=180)
        out = tmp_path / "model.npz"
        save_model(result, out)

        loaded = load_model(out)
        assert loaded.n_components == 3
        assert loaded.version == "test-009"
        assert loaded.corpus_hash == "a" * 64
        assert loaded.sigma_drift == pytest.approx(1.5)
        assert loaded.sigma_virtue == pytest.approx(2.0)

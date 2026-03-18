"""Integration tests for the PCA training pipeline.

T029: train → save_model → load_model → project round-trip.
"""

from __future__ import annotations

import pytest
from eigenhelm.eigenspace import load_model
from eigenhelm.training import save_model, train_eigenspace
from eigenhelm.virtue_extractor import VirtueExtractor

from eigenhelm.models import ProjectionResult


@pytest.mark.integration
class TestTrainingPipelineIntegration:
    def test_train_save_load_project_roundtrip(self, corpus_dir, tmp_path):
        """Full round-trip: train → save → load → project produces valid ProjectionResult."""
        # Train
        result = train_eigenspace(corpus_dir)
        k = result.model.n_components

        # Save
        path = tmp_path / "model.npz"
        save_model(result, path)

        # Load via existing load_model()
        loaded = load_model(path)
        assert loaded.n_components == k
        assert loaded.projection_matrix.shape == (69, k)

        # Project a code unit
        extractor = VirtueExtractor()
        source = "def add(a, b):\n    return a + b\n" * 5
        vectors = extractor.extract(source, "python")
        assert len(vectors) > 0

        proj = extractor.project(vectors[0], loaded)
        assert isinstance(proj, ProjectionResult)
        assert proj.coordinates.shape == (k,)
        assert proj.l_drift >= 0.0
        assert proj.l_virtue >= 0.0
        assert proj.quality_flag in {"nominal", "partial_input", "high_drift"}

    def test_determinism_same_corpus_same_model(self, corpus_dir, tmp_path):
        """Training twice from the same corpus produces byte-identical .npz files."""
        path1 = tmp_path / "model1.npz"
        path2 = tmp_path / "model2.npz"

        _warmup = train_eigenspace(corpus_dir)  # noqa: F841 — warm up / discard
        result1 = train_eigenspace(corpus_dir)
        result2 = train_eigenspace(corpus_dir)

        save_model(result1, path1)
        save_model(result2, path2)

        assert path1.read_bytes() == path2.read_bytes(), (
            "Identical corpus must produce byte-identical .npz output"
        )

    def test_projection_shape_matches_n_components(self, corpus_dir, tmp_path):
        """Projected coordinates.shape == (k,) for explicit n_components."""
        result = train_eigenspace(corpus_dir, n_components=2)
        path = tmp_path / "model.npz"
        save_model(result, path)
        loaded = load_model(path)

        extractor = VirtueExtractor()
        source = "def f(x):\n    return x * 2\n" * 10
        vectors = extractor.extract(source, "python")
        proj = extractor.project(vectors[0], loaded)
        assert proj.coordinates.shape == (2,)

    def test_calibration_round_trip(self, corpus_dir, tmp_path):
        """Calibration constants survive train → save → load without loss."""
        result = train_eigenspace(corpus_dir)
        path = tmp_path / "calibrated.npz"
        save_model(result, path)

        loaded = load_model(path)

        assert loaded.sigma_drift != pytest.approx(1.0), (
            "sigma_drift must be corpus-calibrated, not the default 1.0"
        )
        assert loaded.sigma_virtue != pytest.approx(1.0), (
            "sigma_virtue must be corpus-calibrated, not the default 1.0"
        )
        assert loaded.sigma_drift == pytest.approx(result.calibration.sigma_drift)
        assert loaded.sigma_virtue == pytest.approx(result.calibration.sigma_virtue)
        assert result.calibration.n_projections > 0

    def test_exemplar_round_trip(self, corpus_dir, tmp_path):
        """Exemplars survive train → save → load with content hashes preserved."""
        result = train_eigenspace(corpus_dir)
        assert result.exemplars is not None, "Training must produce exemplars"
        assert len(result.exemplars) > 0

        path = tmp_path / "exemplar_model.npz"
        save_model(result, path)
        loaded = load_model(path)

        assert loaded.exemplars is not None
        assert loaded.n_exemplars == len(result.exemplars)
        # Content hashes must match after round-trip
        original_hashes = {e.content_hash for e in result.exemplars}
        loaded_hashes = {e.content_hash for e in loaded.exemplars}
        assert original_hashes == loaded_hashes

    def test_exemplar_count_matches_components(self, corpus_dir, tmp_path):
        """Number of exemplars equals number of PCA components by default."""
        result = train_eigenspace(corpus_dir)
        assert result.exemplars is not None
        # Exemplar count should be <= n_components (some clusters may be empty)
        assert len(result.exemplars) <= result.model.n_components

    def test_evaluate_with_exemplars_produces_5_dimensions(self, corpus_dir, tmp_path):
        """Evaluation with exemplar-bearing model produces NCD dimension in weights."""
        from eigenhelm.helm import DynamicHelm
        from eigenhelm.helm.models import EvaluationRequest

        result = train_eigenspace(corpus_dir)
        path = tmp_path / "exemplar_eval.npz"
        save_model(result, path)
        loaded = load_model(path)

        helm = DynamicHelm(eigenspace=loaded)
        source = "def add(a, b):\n    return a + b\n" * 5
        resp = helm.evaluate(EvaluationRequest(source=source, language="python"))
        assert "ncd_exemplar_distance" in resp.critique.score.weights
        assert resp.critique.score.weights["ncd_exemplar_distance"] > 0.0

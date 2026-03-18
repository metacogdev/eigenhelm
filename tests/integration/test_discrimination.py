"""Integration tests for cross-language discrimination test suite (009 T027)."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from eigenhelm.eigenspace import make_synthetic_model
from eigenhelm.models import EigenspaceModel
from eigenhelm.validation.discrimination import (
    DiscriminationReport,
    _cohens_d,
    build_summary,
    render_human,
    render_json,
    run_discrimination_test,
)


class TestCohensD:
    """Unit-level tests for the Cohen's d computation."""

    def test_identical_groups_zero_effect(self) -> None:
        a = [1.0, 2.0, 3.0, 4.0, 5.0]
        assert _cohens_d(a, a) == pytest.approx(0.0)

    def test_separated_groups_positive_effect(self) -> None:
        a = [1.0, 2.0, 3.0]
        b = [4.0, 5.0, 6.0]
        d = _cohens_d(a, b)
        assert d > 0  # b > a → positive
        assert d > 2.0  # Large separation

    def test_small_groups_return_zero(self) -> None:
        assert _cohens_d([1.0], [2.0]) == 0.0

    def test_known_effect_size(self) -> None:
        """Two groups with mean diff = 1, sd = 1 → d ≈ 1.0."""
        rng = np.random.default_rng(42)
        a = rng.normal(0.0, 1.0, 100).tolist()
        b = rng.normal(1.0, 1.0, 100).tolist()
        d = _cohens_d(a, b)
        assert 0.8 < d < 1.3  # Allow sampling noise


class TestRunDiscriminationTest:
    """Integration tests for run_discrimination_test()."""

    @pytest.fixture()
    def fixture_model(self) -> EigenspaceModel:
        """A synthetic model with language metadata for testing."""
        model = make_synthetic_model(n_components=3, seed=99)
        # Reconstruct with metadata since make_synthetic_model doesn't set it
        return EigenspaceModel(
            projection_matrix=model.projection_matrix,
            mean=model.mean,
            std=model.std,
            n_components=model.n_components,
            version=model.version,
            corpus_hash=model.corpus_hash,
            sigma_drift=model.sigma_drift,
            sigma_virtue=model.sigma_virtue,
            language="python",
            corpus_class="A",
            n_training_files=50,
        )

    def test_report_structure(self, fixture_model: EigenspaceModel, tmp_path: Path) -> None:
        """run_discrimination_test returns a DiscriminationReport with all fields."""
        in_dir = tmp_path / "in"
        out_dir = tmp_path / "out"
        in_dir.mkdir()
        out_dir.mkdir()

        # Write minimal Python samples
        (in_dir / "sample1.py").write_text("def foo():\n    return 42\n")
        (in_dir / "sample2.py").write_text("def bar(x):\n    return x + 1\n")
        (out_dir / "sample1.py").write_text("def baz():\n    pass\n")
        (out_dir / "sample2.py").write_text("def qux(y):\n    return y * 2\n")

        report = run_discrimination_test(fixture_model, in_dir, out_dir)

        assert isinstance(report, DiscriminationReport)
        assert report.language == "python"
        assert report.corpus_class == "A"
        assert report.n_components == 3
        assert np.isfinite(report.mean_in_score)
        assert np.isfinite(report.mean_out_score)
        assert np.isfinite(report.effect_size)
        assert isinstance(report.passed, bool)

    def test_empty_dirs_produce_nan(self, fixture_model: EigenspaceModel, tmp_path: Path) -> None:
        """Empty sample directories produce NaN scores gracefully."""
        in_dir = tmp_path / "in"
        out_dir = tmp_path / "out"
        in_dir.mkdir()
        out_dir.mkdir()

        report = run_discrimination_test(fixture_model, in_dir, out_dir)
        assert np.isnan(report.mean_in_score)
        assert np.isnan(report.mean_out_score)
        assert report.effect_size == 0.0
        assert report.passed is False


class TestSummaryAndRendering:
    """Integration tests for summary building and rendering."""

    def test_summary_aggregation(self) -> None:
        reports = [
            DiscriminationReport("python", "A", 5, 0.92, 1.5, 2.0, 0.2, 0.55, 0.82, True),
            DiscriminationReport("javascript", "A", 4, 0.91, 1.3, 1.8, 0.25, 0.60, 0.71, True),
            DiscriminationReport("typescript", "A", 4, 0.90, 1.2, 1.7, 0.28, 0.58, 0.65, True),
            DiscriminationReport("go", "A", 3, 0.89, 1.1, 1.5, 0.30, 0.55, 0.60, True),
            DiscriminationReport("rust", "A", 4, 0.91, 1.4, 1.9, 0.22, 0.57, 0.73, True),
        ]
        summary = build_summary(reports)
        assert len(summary.reports) == 5
        assert summary.all_passed is True

    def test_render_human_complete(self) -> None:
        reports = [
            DiscriminationReport("python", "A", 5, 0.92, 1.5, 2.0, 0.2, 0.55, 0.82, True),
            DiscriminationReport("go", "A", 3, 0.88, 1.0, 1.0, 0.4, 0.45, 0.3, False),
        ]
        summary = build_summary(reports)
        output = render_human(summary)

        assert "python" in output
        assert "go" in output
        assert "PASS" in output
        assert "FAIL" in output
        assert "SOME FAILED" in output

    def test_render_json_roundtrip(self) -> None:
        reports = [
            DiscriminationReport("python", "A", 5, 0.92, 1.5, 2.0, 0.2, 0.55, 0.82, True),
        ]
        summary = build_summary(reports)
        output = render_json(summary)

        data = json.loads(output)
        assert data["all_passed"] is True
        assert len(data["reports"]) == 1
        assert data["reports"][0]["language"] == "python"
        assert data["reports"][0]["effect_size"] == 0.82

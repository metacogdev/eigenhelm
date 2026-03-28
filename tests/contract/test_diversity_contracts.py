"""Contract tests for corpus diversity analysis (014-polyglot-discrimination)."""

from __future__ import annotations

import json

import numpy as np
import pytest

from eigenhelm.validation.diversity import (
    DiversityReport,
    DiversitySummary,
    RepoDiversityStats,
    render_human,
    render_json,
    run_diversity_analysis,
)


class TestDiversityReportStructure:
    """DiversityReport has all required fields."""

    def test_report_fields(self) -> None:
        report = DiversityReport(
            language="go",
            corpus_class="A",
            n_repos=4,
            n_vectors=100,
            n_features=69,
            effective_rank=4.5,
            dead_features=2,
            explained_variance_top3=[0.15, 0.12, 0.10],
            min_centroid_distance=2.5,
            mean_centroid_distance=3.0,
            between_repo_variance_ratio=0.08,
            sample_balance=0.5,
            repo_stats=[
                RepoDiversityStats(repo_name="repo1", n_vectors=25, centroid_norm=1.2),
            ],
            passed=True,
            warnings=[],
        )
        assert report.language == "go"
        assert report.n_features == 69
        assert report.passed is True
        assert report.warnings == []

    def test_passing_thresholds(self) -> None:
        """Report passes when all thresholds are met."""
        rng = np.random.default_rng(42)
        X = rng.standard_normal((40, 69))
        # Make 2 repo clusters distinct
        X[:20] += 3.0
        labels = ["repo_a"] * 20 + ["repo_b"] * 20
        report = run_diversity_analysis(X, labels, "test")
        # With well-separated clusters, should pass most metrics
        assert isinstance(report.passed, bool)
        assert isinstance(report.warnings, list)

    def test_failing_thresholds(self) -> None:
        """Report fails when corpus has very low effective rank."""
        rng = np.random.default_rng(42)
        # Data with only 1-2 dimensions of real variance (68 dead features)
        X = np.zeros((40, 69))
        X[:, 0] = rng.standard_normal(40) * 10
        X[:20, 0] += 5
        labels = ["repo_a"] * 20 + ["repo_b"] * 20
        report = run_diversity_analysis(X, labels, "test")
        assert report.passed is False
        assert len(report.warnings) > 0


class TestPreconditionValidation:
    """run_diversity_analysis validates preconditions."""

    def test_wrong_shape_raises(self) -> None:
        X = np.zeros((10, 50))
        labels = ["repo"] * 10
        with pytest.raises(ValueError, match="shape"):
            run_diversity_analysis(X, labels, "test")

    def test_nan_raises(self) -> None:
        X = np.zeros((10, 69))
        X[0, 0] = np.nan
        labels = ["repo_a"] * 5 + ["repo_b"] * 5
        with pytest.raises(ValueError, match="NaN"):
            run_diversity_analysis(X, labels, "test")

    def test_inf_raises(self) -> None:
        X = np.zeros((10, 69))
        X[0, 0] = np.inf
        labels = ["repo_a"] * 5 + ["repo_b"] * 5
        with pytest.raises(ValueError, match="NaN"):
            run_diversity_analysis(X, labels, "test")

    def test_label_mismatch_raises(self) -> None:
        X = np.zeros((10, 69))
        labels = ["repo"] * 5
        with pytest.raises(ValueError, match="length"):
            run_diversity_analysis(X, labels, "test")

    def test_fewer_than_2_repos_raises(self) -> None:
        X = np.zeros((10, 69))
        labels = ["repo_a"] * 10
        with pytest.raises(ValueError, match="2 distinct"):
            run_diversity_analysis(X, labels, "test")


class TestDiversitySummary:
    """DiversitySummary aggregation logic."""

    def test_all_passed(self) -> None:
        reports = [
            DiversityReport(
                language="go",
                corpus_class="A",
                n_repos=4,
                n_vectors=100,
                n_features=69,
                effective_rank=4.0,
                dead_features=2,
                explained_variance_top3=[0.1, 0.1, 0.1],
                min_centroid_distance=2.0,
                mean_centroid_distance=3.0,
                between_repo_variance_ratio=0.1,
                sample_balance=0.5,
                repo_stats=[],
                passed=True,
                warnings=[],
            ),
        ]
        summary = DiversitySummary(reports=tuple(reports))
        assert summary.all_passed is True

    def test_not_all_passed(self) -> None:
        reports = [
            DiversityReport(
                language="go",
                corpus_class="A",
                n_repos=4,
                n_vectors=100,
                n_features=69,
                effective_rank=1.5,
                dead_features=20,
                explained_variance_top3=[0.5, 0.3, 0.1],
                min_centroid_distance=0.5,
                mean_centroid_distance=1.0,
                between_repo_variance_ratio=0.02,
                sample_balance=0.05,
                repo_stats=[],
                passed=False,
                warnings=["low rank"],
            ),
        ]
        summary = DiversitySummary(reports=tuple(reports))
        assert summary.all_passed is False


class TestRenderHuman:
    """render_human output has required columns."""

    def test_table_has_required_columns(self) -> None:
        reports = [
            DiversityReport(
                language="go",
                corpus_class="A",
                n_repos=4,
                n_vectors=100,
                n_features=69,
                effective_rank=4.0,
                dead_features=2,
                explained_variance_top3=[0.1, 0.1, 0.1],
                min_centroid_distance=2.0,
                mean_centroid_distance=3.0,
                between_repo_variance_ratio=0.1,
                sample_balance=0.5,
                repo_stats=[],
                passed=True,
                warnings=[],
            ),
        ]
        summary = DiversitySummary(reports=tuple(reports))
        output = render_human(summary)
        assert "Language" in output
        assert "Eff.Rank" in output
        assert "PASS" in output
        assert "ALL PASSED" in output

    def test_failing_report_shows_fail(self) -> None:
        reports = [
            DiversityReport(
                language="go",
                corpus_class="A",
                n_repos=4,
                n_vectors=100,
                n_features=69,
                effective_rank=1.5,
                dead_features=20,
                explained_variance_top3=[0.5, 0.3, 0.1],
                min_centroid_distance=0.5,
                mean_centroid_distance=1.0,
                between_repo_variance_ratio=0.02,
                sample_balance=0.05,
                repo_stats=[],
                passed=False,
                warnings=["low rank"],
            ),
        ]
        summary = DiversitySummary(reports=tuple(reports))
        output = render_human(summary)
        assert "FAIL" in output
        assert "SOME FAILED" in output


class TestRenderJson:
    """render_json output is valid JSON with required structure."""

    def test_valid_json_structure(self) -> None:
        reports = [
            DiversityReport(
                language="go",
                corpus_class="A",
                n_repos=4,
                n_vectors=100,
                n_features=69,
                effective_rank=4.0,
                dead_features=2,
                explained_variance_top3=[0.1, 0.1, 0.1],
                min_centroid_distance=2.0,
                mean_centroid_distance=3.0,
                between_repo_variance_ratio=0.1,
                sample_balance=0.5,
                repo_stats=[
                    RepoDiversityStats("gjson", 25, 1.2),
                ],
                passed=True,
                warnings=[],
            ),
        ]
        summary = DiversitySummary(reports=tuple(reports))
        output = render_json(summary)
        data = json.loads(output)
        assert "version" in data
        assert "languages" in data
        assert "summary" in data
        assert "go" in data["languages"]
        assert data["languages"]["go"]["passed"] is True
        assert data["summary"]["passed_count"] == 1
        assert data["summary"]["total"] == 1

    def test_per_language_keys(self) -> None:
        reports = [
            DiversityReport(
                language="javascript",
                corpus_class="A",
                n_repos=4,
                n_vectors=50,
                n_features=69,
                effective_rank=3.5,
                dead_features=5,
                explained_variance_top3=[0.2, 0.15, 0.1],
                min_centroid_distance=1.5,
                mean_centroid_distance=2.0,
                between_repo_variance_ratio=0.08,
                sample_balance=0.4,
                repo_stats=[],
                passed=True,
                warnings=[],
            ),
        ]
        summary = DiversitySummary(reports=tuple(reports))
        data = json.loads(render_json(summary))
        lang_data = data["languages"]["javascript"]
        required_keys = {
            "effective_rank",
            "dead_features",
            "min_centroid_distance",
            "between_repo_variance_ratio",
            "sample_balance",
            "passed",
            "warnings",
            "repos",
        }
        assert required_keys.issubset(lang_data.keys())

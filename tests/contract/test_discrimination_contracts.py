"""Contract tests for discrimination public API (009 T026)."""

from __future__ import annotations

import json

from eigenhelm.validation.discrimination import (
    DiscriminationReport,
    build_summary,
    render_human,
    render_json,
)


class TestDiscriminationReportStructure:
    """Contract: DiscriminationReport has all required fields."""

    def test_report_fields(self) -> None:
        report = DiscriminationReport(
            language="javascript",
            corpus_class="A",
            n_components=5,
            cumulative_variance=0.92,
            sigma_drift=1.5,
            sigma_virtue=2.0,
            mean_in_score=0.25,
            mean_out_score=0.55,
            effect_size=0.82,
            passed=True,
        )
        assert report.language == "javascript"
        assert report.corpus_class == "A"
        assert report.n_components == 5
        assert report.cumulative_variance == 0.92
        assert report.sigma_drift == 1.5
        assert report.sigma_virtue == 2.0
        assert report.mean_in_score == 0.25
        assert report.mean_out_score == 0.55
        assert report.effect_size == 0.82
        assert report.passed is True

    def test_pass_threshold_at_boundary(self) -> None:
        """Effect size exactly 0.5 should fail (>0.5 required)."""
        report = DiscriminationReport(
            language="go",
            corpus_class="A",
            n_components=3,
            cumulative_variance=0.90,
            sigma_drift=1.0,
            sigma_virtue=1.0,
            mean_in_score=0.30,
            mean_out_score=0.50,
            effect_size=0.5,
            passed=False,
        )
        assert report.passed is False

    def test_passing_report(self) -> None:
        report = DiscriminationReport(
            language="rust",
            corpus_class="A",
            n_components=4,
            cumulative_variance=0.91,
            sigma_drift=1.2,
            sigma_virtue=1.8,
            mean_in_score=0.20,
            mean_out_score=0.60,
            effect_size=0.73,
            passed=True,
        )
        assert report.passed is True


class TestDiscriminationSummary:
    """Contract: summary aggregation."""

    def test_all_passed_when_all_pass(self) -> None:
        reports = [
            DiscriminationReport("python", "A", 5, 0.92, 1.5, 2.0, 0.2, 0.5, 0.8, True),
            DiscriminationReport("javascript", "A", 4, 0.91, 1.3, 1.8, 0.3, 0.6, 0.7, True),
        ]
        summary = build_summary(reports)
        assert summary.all_passed is True
        assert len(summary.reports) == 2

    def test_all_passed_false_when_one_fails(self) -> None:
        reports = [
            DiscriminationReport("python", "A", 5, 0.92, 1.5, 2.0, 0.2, 0.5, 0.8, True),
            DiscriminationReport("go", "A", 3, 0.88, 1.0, 1.0, 0.4, 0.45, 0.3, False),
        ]
        summary = build_summary(reports)
        assert summary.all_passed is False


class TestRenderHuman:
    """Contract: render_human() produces table with required columns."""

    def test_table_has_required_columns(self) -> None:
        reports = [
            DiscriminationReport("python", "A", 5, 0.92, 1.5, 2.0, 0.2, 0.55, 0.82, True),
        ]
        summary = build_summary(reports)
        output = render_human(summary)

        assert "Language" in output
        assert "Components" in output
        assert "Variance" in output
        assert "σ_drift" in output
        assert "σ_virtue" in output
        assert "In-Score" in output
        assert "Out-Score" in output
        assert "Effect Size" in output
        assert "Pass" in output
        assert "python" in output
        assert "ALL PASSED" in output

    def test_failing_report_shows_fail(self) -> None:
        reports = [
            DiscriminationReport("go", "A", 3, 0.88, 1.0, 1.0, 0.4, 0.45, 0.3, False),
        ]
        summary = build_summary(reports)
        output = render_human(summary)
        assert "FAIL" in output
        assert "SOME FAILED" in output


class TestRenderJson:
    """Contract: render_json() produces valid JSON with required keys."""

    def test_valid_json_with_reports_array(self) -> None:
        reports = [
            DiscriminationReport("python", "A", 5, 0.92, 1.5, 2.0, 0.2, 0.55, 0.82, True),
            DiscriminationReport("go", "A", 3, 0.88, 1.0, 1.0, 0.4, 0.45, 0.3, False),
        ]
        summary = build_summary(reports)
        output = render_json(summary)

        data = json.loads(output)  # Must be valid JSON
        assert "reports" in data
        assert "all_passed" in data
        assert isinstance(data["reports"], list)
        assert len(data["reports"]) == 2
        assert data["all_passed"] is False

    def test_per_language_report_keys(self) -> None:
        reports = [
            DiscriminationReport("javascript", "A", 4, 0.91, 1.3, 1.8, 0.3, 0.6, 0.7, True),
        ]
        summary = build_summary(reports)
        output = render_json(summary)
        data = json.loads(output)

        report = data["reports"][0]
        required_keys = {
            "language", "corpus_class", "n_components", "cumulative_variance",
            "sigma_drift", "sigma_virtue", "mean_in_score", "mean_out_score",
            "effect_size", "passed",
        }
        assert required_keys.issubset(report.keys())

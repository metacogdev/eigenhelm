"""Integration tests for the use case benchmark harness (018, T015)."""

from __future__ import annotations

import json
from pathlib import Path


from eigenhelm.helm import DynamicHelm
from eigenhelm.validation.categorize import categorize_directory
from eigenhelm.validation.usecase_benchmark import UseCaseBenchmark
from eigenhelm.validation.usecase_benchmark import compare_reports
from eigenhelm.validation.usecase_models import BenchmarkReport, FileCategory

FIXTURE_DIR = Path(__file__).parent.parent / "fixtures" / "usecase_benchmark" / "good"


class TestFileCategorizationOnFixtures:
    """Verify categorization works on the test fixtures."""

    def test_categorize_fixture_directory(self) -> None:
        results = categorize_directory(FIXTURE_DIR)
        categories = {path.name: cat for path, cat in results.items()}

        assert categories.get("implementation.py") == FileCategory.IMPLEMENTATION
        assert categories.get("test_example.py") == FileCategory.TEST
        assert categories.get("__init__.py") == FileCategory.INIT
        assert categories.get("generated_pb2.py") == FileCategory.GENERATED

    def test_at_least_3_categories(self) -> None:
        results = categorize_directory(FIXTURE_DIR)
        unique_categories = {cat for cat in results.values()}
        assert len(unique_categories) >= 3


class TestUseCaseBenchmark:
    """Integration test for the benchmark harness against test fixtures."""

    def test_run_produces_report(self) -> None:
        helm = DynamicHelm()  # no model — low confidence mode
        benchmark = UseCaseBenchmark(helm=helm, model_name="none", model_version="test")
        benchmark.add_project(FIXTURE_DIR, name="test-fixtures")
        report = benchmark.run()

        assert isinstance(report, BenchmarkReport)
        assert report.n_files > 0
        assert report.n_projects == 1

    def test_report_has_categories(self) -> None:
        helm = DynamicHelm()
        benchmark = UseCaseBenchmark(helm=helm)
        benchmark.add_project(FIXTURE_DIR, name="test-fixtures")
        report = benchmark.run()

        assert len(report.categories) >= 2
        cat_names = {c.category for c in report.categories}
        assert FileCategory.IMPLEMENTATION in cat_names

    def test_report_serializes_to_json(self) -> None:
        helm = DynamicHelm()
        benchmark = UseCaseBenchmark(helm=helm)
        benchmark.add_project(FIXTURE_DIR, name="test-fixtures")
        report = benchmark.run()

        json_str = report.to_json()
        data = json.loads(json_str)
        assert "categories" in data
        assert "targets" in data
        assert isinstance(data["categories"], list)

    def test_report_renders_human(self) -> None:
        helm = DynamicHelm()
        benchmark = UseCaseBenchmark(helm=helm)
        benchmark.add_project(FIXTURE_DIR, name="test-fixtures")
        report = benchmark.run()

        text = report.render()
        assert "Per-Category Score Distributions" in text
        assert "Quality Targets" in text

    def test_targets_include_sc001_and_sc002(self) -> None:
        helm = DynamicHelm()
        benchmark = UseCaseBenchmark(helm=helm)
        benchmark.add_project(FIXTURE_DIR, name="test-fixtures")
        report = benchmark.run()

        target_names = {t.name for t in report.targets}
        assert "sc_001_file_count" in target_names
        assert "sc_002_impl_vs_init_gap" in target_names


class TestReportComparison:
    """Integration test for regression detection between reports."""

    def test_no_regressions_when_identical(self) -> None:
        helm = DynamicHelm()
        benchmark = UseCaseBenchmark(helm=helm)
        benchmark.add_project(FIXTURE_DIR, name="test-fixtures")
        report = benchmark.run()

        alerts = compare_reports(report, report)
        assert alerts == []

    def test_regression_detected_on_target_failure(self) -> None:
        """When a baseline target was met but current is not, flag regression."""
        from dataclasses import replace

        helm = DynamicHelm()
        benchmark = UseCaseBenchmark(helm=helm)
        benchmark.add_project(FIXTURE_DIR, name="test-fixtures")
        report = benchmark.run()

        # Create a baseline where sc_001 was met (had 1000 files)
        good_targets = tuple(
            replace(t, baseline=1000.0) if t.name == "sc_001_file_count" else t
            for t in report.targets
        )
        baseline = replace(report, targets=good_targets)

        alerts = compare_reports(report, baseline)
        sc001_alerts = [a for a in alerts if a.target_name == "sc_001_file_count"]
        # Current report has < 500 files, baseline had 1000 → regression
        assert len(sc001_alerts) > 0

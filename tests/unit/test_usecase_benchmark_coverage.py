"""Unit tests for usecase_benchmark functions (validation/usecase_benchmark.py).

Targets uncovered functions: sync_corpus, _discover_source_files,
_compute_distribution, _signal_quality_label, _compute_dimension_discrimination,
compute_fp_fn, add_fp_fn_targets, add_replay_target, add_attribution_target,
compute_noise_rate, and compare_reports edge cases.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from eigenhelm.validation.usecase_benchmark import (
    UseCaseBenchmark,
    _compute_distribution,
    _compute_dimension_discrimination,
    _commit_replay_result,
    _dimension_metric,
    _discover_source_files,
    _regression_change,
    _signal_quality_label,
    add_attribution_target,
    add_fp_fn_targets,
    add_replay_target,
    compare_reports,
    compute_fp_fn,
    compute_noise_rate,
    sync_corpus,
)
from eigenhelm.validation.usecase_models import (
    BenchmarkReport,
    CategoryDistribution,
    CommitReplayResult,
    FileCategory,
    FileEvaluation,
    QualityTarget,
)


class TestSyncCorpus:
    """Tests for sync_corpus that clones projects from a TOML manifest."""

    def test_clone_new_project(self, tmp_path: Path) -> None:
        manifest = tmp_path / "manifest.toml"
        manifest.write_text(
            '[[projects]]\nname = "proj-a"\nurl = "https://example.com/proj-a.git"\n'
        )
        target_dir = tmp_path / "repos"

        with patch("eigenhelm.validation.usecase_benchmark.subprocess") as mock_sub:
            mock_sub.run.return_value = MagicMock(returncode=0)
            projects = sync_corpus(manifest, target_dir)

        assert len(projects) == 1
        assert projects[0]["name"] == "proj-a"
        assert target_dir.is_dir()
        # Should have called git clone
        mock_sub.run.assert_called_once()
        call_args = mock_sub.run.call_args[0][0]
        assert "clone" in call_args

    def test_skip_existing_project(self, tmp_path: Path) -> None:
        manifest = tmp_path / "manifest.toml"
        manifest.write_text(
            '[[projects]]\nname = "proj-a"\nurl = "https://example.com/proj-a.git"\n'
        )
        target_dir = tmp_path / "repos"
        (target_dir / "proj-a").mkdir(parents=True)

        with patch("eigenhelm.validation.usecase_benchmark.subprocess") as mock_sub:
            projects = sync_corpus(manifest, target_dir)

        # Should NOT have called git clone since dir already exists
        mock_sub.run.assert_not_called()
        assert len(projects) == 1

    def test_clone_with_commit(self, tmp_path: Path) -> None:
        manifest = tmp_path / "manifest.toml"
        manifest.write_text(
            "[[projects]]\n"
            'name = "proj-b"\n'
            'url = "https://example.com/proj-b.git"\n'
            'commit = "abc123"\n'
        )
        target_dir = tmp_path / "repos"

        with patch("eigenhelm.validation.usecase_benchmark.subprocess") as mock_sub:
            mock_sub.run.return_value = MagicMock(returncode=0)
            sync_corpus(manifest, target_dir)

        # clone + fetch + checkout = 3 calls
        assert mock_sub.run.call_count == 3


class TestDiscoverSourceFiles:
    """Tests for _discover_source_files."""

    def test_discovers_python_files(self, tmp_path: Path) -> None:
        (tmp_path / "main.py").write_text("x = 1")
        (tmp_path / "lib.py").write_text("y = 2")
        (tmp_path / "readme.md").write_text("# docs")
        results = _discover_source_files(tmp_path)
        py_files = [p for p, lang in results if p.suffix == ".py"]
        assert len(py_files) == 2
        assert all(lang == "python" for _, lang in results)

    def test_skips_hidden_and_venv_dirs(self, tmp_path: Path) -> None:
        (tmp_path / ".git").mkdir()
        (tmp_path / ".git" / "config.py").write_text("")
        (tmp_path / ".venv").mkdir()
        (tmp_path / ".venv" / "lib.py").write_text("")
        (tmp_path / "node_modules").mkdir()
        (tmp_path / "node_modules" / "index.js").write_text("")
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "app.py").write_text("x = 1")

        results = _discover_source_files(tmp_path)
        paths = [str(p) for p, _ in results]
        assert any("app.py" in p for p in paths)
        assert not any(".git" in p for p in paths)
        assert not any(".venv" in p for p in paths)
        assert not any("node_modules" in p for p in paths)

    def test_src_dir_override(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        src.mkdir()
        (src / "main.py").write_text("x = 1")
        (tmp_path / "other.py").write_text("y = 2")

        results = _discover_source_files(tmp_path, src_dir="src")
        # Should only find files under src/
        paths = [str(p) for p, _ in results]
        assert any("main.py" in p for p in paths)
        # 'other.py' is outside src_dir, so it should not be found
        assert not any("other.py" in p for p in paths)

    def test_src_dir_fallback(self, tmp_path: Path) -> None:
        """When src_dir doesn't exist, falls back to project_dir."""
        (tmp_path / "main.py").write_text("x = 1")
        results = _discover_source_files(tmp_path, src_dir="nonexistent")
        assert len(results) == 1

    def test_skips_symlinks(self, tmp_path: Path) -> None:
        (tmp_path / "real.py").write_text("x = 1")
        link = tmp_path / "link.py"
        link.symlink_to(tmp_path / "real.py")
        results = _discover_source_files(tmp_path)
        names = [p.name for p, _ in results]
        assert "real.py" in names
        assert "link.py" not in names

    def test_skips_egg_info(self, tmp_path: Path) -> None:
        egg = tmp_path / "pkg.egg-info"
        egg.mkdir()
        (egg / "top_level.py").write_text("")
        (tmp_path / "main.py").write_text("x = 1")
        results = _discover_source_files(tmp_path)
        names = [p.name for p, _ in results]
        assert "main.py" in names
        assert "top_level.py" not in names


class TestComputeDistribution:
    """Tests for _compute_distribution."""

    def test_basic_distribution(self) -> None:
        scores = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        dist = _compute_distribution(scores, FileCategory.IMPLEMENTATION)
        assert dist.category == FileCategory.IMPLEMENTATION
        assert dist.n_files == 10
        assert dist.min == pytest.approx(0.1)
        assert dist.max == pytest.approx(1.0)
        assert dist.median == pytest.approx(0.55)

    def test_single_score(self) -> None:
        dist = _compute_distribution([0.5], FileCategory.TEST)
        assert dist.n_files == 1
        assert dist.min == dist.max == pytest.approx(0.5)


class TestSignalQualityLabel:
    """Tests for _signal_quality_label."""

    def test_none_is_noise(self) -> None:
        assert _signal_quality_label(None) == "noise"

    def test_strong_signal(self) -> None:
        assert _signal_quality_label(0.9) == "strong"
        assert _signal_quality_label(-0.9) == "strong"

    def test_medium_signal(self) -> None:
        assert _signal_quality_label(0.6) == "medium"
        assert _signal_quality_label(-0.6) == "medium"

    def test_weak_signal(self) -> None:
        assert _signal_quality_label(0.3) == "weak"
        assert _signal_quality_label(-0.3) == "weak"

    def test_noise_signal(self) -> None:
        assert _signal_quality_label(0.1) == "noise"
        assert _signal_quality_label(0.0) == "noise"

    def test_boundary_values(self) -> None:
        assert _signal_quality_label(0.8) == "medium"  # not > 0.8
        assert _signal_quality_label(0.81) == "strong"
        assert _signal_quality_label(0.5) == "weak"  # not > 0.5
        assert _signal_quality_label(0.51) == "medium"
        assert _signal_quality_label(0.2) == "noise"  # not > 0.2
        assert _signal_quality_label(0.21) == "weak"


class TestComputeDimensionDiscrimination:
    """Tests for _compute_dimension_discrimination."""

    def test_empty_evaluations(self) -> None:
        results = _compute_dimension_discrimination([])
        assert results == []

    def test_single_category_too_few(self) -> None:
        evals = [
            FileEvaluation(
                file_path="a.py",
                project="p",
                category=FileCategory.IMPLEMENTATION,
                score=0.5,
                decision="accept",
                dim_scores={"manifold_drift": 0.3},
            )
        ]
        results = _compute_dimension_discrimination(evals)
        # Only 1 eval per category, need >= 2
        assert results == []

    def test_implementation_category(self) -> None:
        evals = [
            FileEvaluation(
                file_path=f"f{i}.py",
                project="p",
                category=FileCategory.IMPLEMENTATION,
                score=0.3 + i * 0.1,
                decision="accept",
                dim_scores={"manifold_drift": 0.2 + i * 0.1, "token_entropy": 0.5},
            )
            for i in range(3)
        ]
        results = _compute_dimension_discrimination(evals)
        assert len(results) > 0
        dims = [r.dimension for r in results]
        assert "manifold_drift" in dims

    def test_dimension_metric_helper(self) -> None:
        evals = [
            FileEvaluation(
                file_path=f"f{i}.py",
                project="p",
                category=FileCategory.TEST,
                score=0.3 + i * 0.1,
                decision="accept",
                dim_scores={"token_entropy": 0.2 + i * 0.1},
            )
            for i in range(3)
        ]
        metric = _dimension_metric(evals, "token_entropy", FileCategory.TEST)
        assert metric.dimension == "token_entropy"
        assert metric.category == FileCategory.TEST
        assert metric.cohens_d is None
        assert metric.mean == pytest.approx(0.3)

    def test_cohens_d_computed_for_large_impl_set(self) -> None:
        """With >= 10 implementation files, Cohen's d should be computed."""
        evals = [
            FileEvaluation(
                file_path=f"f{i}.py",
                project="p",
                category=FileCategory.IMPLEMENTATION,
                score=i * 0.05,
                decision="accept",
                dim_scores={
                    "manifold_drift": i * 0.1,
                    "manifold_alignment": 0.5,
                    "token_entropy": 0.5,
                    "compression_structure": 0.5,
                    "ncd_exemplar_distance": 0.5,
                },
            )
            for i in range(12)
        ]
        results = _compute_dimension_discrimination(evals)
        impl_results = [r for r in results if r.category == FileCategory.IMPLEMENTATION]
        # At least one dimension should have a non-None Cohen's d
        drift_result = next(r for r in impl_results if r.dimension == "manifold_drift")
        assert drift_result.cohens_d is not None

    def test_multiple_categories(self) -> None:
        evals = [
            FileEvaluation(
                "a.py",
                "p",
                FileCategory.IMPLEMENTATION,
                0.5,
                "accept",
                dim_scores={"manifold_drift": 0.3},
            ),
            FileEvaluation(
                "b.py",
                "p",
                FileCategory.IMPLEMENTATION,
                0.6,
                "accept",
                dim_scores={"manifold_drift": 0.4},
            ),
            FileEvaluation(
                "t1.py",
                "p",
                FileCategory.TEST,
                0.7,
                "accept",
                dim_scores={"manifold_drift": 0.5},
            ),
            FileEvaluation(
                "t2.py",
                "p",
                FileCategory.TEST,
                0.8,
                "accept",
                dim_scores={"manifold_drift": 0.6},
            ),
        ]
        results = _compute_dimension_discrimination(evals)
        categories = {r.category for r in results}
        assert FileCategory.IMPLEMENTATION in categories
        assert FileCategory.TEST in categories


class TestComputeFpFn:
    """Tests for compute_fp_fn."""

    def test_basic_fp_fn(self) -> None:
        good = [
            FileEvaluation("a.py", "p", FileCategory.IMPLEMENTATION, 0.5, "accept"),
            FileEvaluation("b.py", "p", FileCategory.IMPLEMENTATION, 0.3, "reject"),
        ]
        bad = [
            FileEvaluation("c.py", "p", FileCategory.IMPLEMENTATION, 0.7, "reject"),
            FileEvaluation("d.py", "p", FileCategory.IMPLEMENTATION, 0.2, "accept"),
        ]
        fp, fn = compute_fp_fn(good, bad)
        assert fp == pytest.approx(0.5)  # 1 of 2 good rejected
        assert fn == pytest.approx(0.5)  # 1 of 2 bad accepted

    def test_empty_lists(self) -> None:
        fp, fn = compute_fp_fn([], [])
        assert fp is None
        assert fn is None

    def test_impl_only_filter(self) -> None:
        good = [
            FileEvaluation("a.py", "p", FileCategory.IMPLEMENTATION, 0.5, "reject"),
            FileEvaluation("t.py", "p", FileCategory.TEST, 0.3, "reject"),
        ]
        bad = [
            FileEvaluation("c.py", "p", FileCategory.IMPLEMENTATION, 0.7, "accept"),
            FileEvaluation("d.py", "p", FileCategory.TEST, 0.2, "accept"),
        ]
        fp, fn = compute_fp_fn(good, bad, impl_only=True)
        assert fp == pytest.approx(1.0)  # 1/1 impl good rejected
        assert fn == pytest.approx(1.0)  # 1/1 impl bad accepted

    def test_no_rejects_zero_fp(self) -> None:
        good = [
            FileEvaluation("a.py", "p", FileCategory.IMPLEMENTATION, 0.5, "accept"),
        ]
        fp, fn = compute_fp_fn(good, [])
        assert fp == pytest.approx(0.0)
        assert fn is None


class TestAddFpFnTargets:
    """Tests for add_fp_fn_targets."""

    def test_adds_sc004_sc005(self) -> None:
        report = BenchmarkReport()
        updated = add_fp_fn_targets(report, 0.15, 0.35)
        target_names = {t.name for t in updated.targets}
        assert "sc_004_fp_rate" in target_names
        assert "sc_005_fn_rate" in target_names
        assert updated.fp_rate == 0.15
        assert updated.fn_rate == 0.35

    def test_targets_pass_when_below_threshold(self) -> None:
        report = BenchmarkReport()
        updated = add_fp_fn_targets(report, 0.10, 0.30)
        sc004 = next(t for t in updated.targets if t.name == "sc_004_fp_rate")
        sc005 = next(t for t in updated.targets if t.name == "sc_005_fn_rate")
        assert sc004.met  # 0.10 <= 0.20
        assert sc005.met  # 0.30 <= 0.40

    def test_targets_fail_when_above_threshold(self) -> None:
        report = BenchmarkReport()
        updated = add_fp_fn_targets(report, 0.25, 0.50)
        sc004 = next(t for t in updated.targets if t.name == "sc_004_fp_rate")
        sc005 = next(t for t in updated.targets if t.name == "sc_005_fn_rate")
        assert not sc004.met
        assert not sc005.met

    def test_none_rates(self) -> None:
        report = BenchmarkReport()
        updated = add_fp_fn_targets(report, None, None)
        sc004 = next(t for t in updated.targets if t.name == "sc_004_fp_rate")
        assert not sc004.met  # None baseline => not met


class TestAddReplayTarget:
    """Tests for add_replay_target."""

    def test_adds_sc007(self) -> None:
        report = BenchmarkReport()
        updated = add_replay_target(report, 0.03)
        target_names = {t.name for t in updated.targets}
        assert "sc_007_noise_rate" in target_names
        sc007 = next(t for t in updated.targets if t.name == "sc_007_noise_rate")
        assert sc007.met  # 0.03 <= 0.06

    def test_fails_when_above_threshold(self) -> None:
        report = BenchmarkReport()
        updated = add_replay_target(report, 0.10)
        sc007 = next(t for t in updated.targets if t.name == "sc_007_noise_rate")
        assert not sc007.met


class TestAddAttributionTarget:
    """Tests for add_attribution_target."""

    def test_adds_sc006(self) -> None:
        report = BenchmarkReport()
        updated = add_attribution_target(report, 0.75)
        target_names = {t.name for t in updated.targets}
        assert "sc_006_attribution_precision" in target_names
        assert updated.attribution_precision == 0.75
        sc006 = next(
            t for t in updated.targets if t.name == "sc_006_attribution_precision"
        )
        assert sc006.met  # 0.75 >= 0.60

    def test_fails_when_below_threshold(self) -> None:
        report = BenchmarkReport()
        updated = add_attribution_target(report, 0.40)
        sc006 = next(
            t for t in updated.targets if t.name == "sc_006_attribution_precision"
        )
        assert not sc006.met

    def test_none_precision(self) -> None:
        report = BenchmarkReport()
        updated = add_attribution_target(report, None)
        sc006 = next(
            t for t in updated.targets if t.name == "sc_006_attribution_precision"
        )
        assert not sc006.met


class TestComputeNoiseRate:
    """Tests for compute_noise_rate."""

    def test_no_replays(self) -> None:
        assert compute_noise_rate([]) == pytest.approx(0.0)

    def test_all_noise(self) -> None:
        replays = [
            CommitReplayResult("abc", 3, 2, 2, True),
            CommitReplayResult("def", 5, 1, 1, True),
        ]
        assert compute_noise_rate(replays) == pytest.approx(1.0)

    def test_no_noise(self) -> None:
        replays = [
            CommitReplayResult("abc", 3, 2, 0, False),
            CommitReplayResult("def", 5, 3, 1, False),
        ]
        assert compute_noise_rate(replays) == pytest.approx(0.0)

    def test_mixed(self) -> None:
        replays = [
            CommitReplayResult("abc", 3, 2, 2, True),
            CommitReplayResult("def", 5, 3, 1, False),
            CommitReplayResult("ghi", 2, 1, 1, True),
            CommitReplayResult("jkl", 4, 0, 0, False),
        ]
        assert compute_noise_rate(replays) == pytest.approx(0.5)

    def test_commit_replay_result_helper(self) -> None:
        evaluations = [
            FileEvaluation("test_a.py", "example", FileCategory.TEST, 0.7, "reject"),
            FileEvaluation(
                "main.py", "example", FileCategory.IMPLEMENTATION, 0.2, "accept"
            ),
        ]
        result = _commit_replay_result("abc", evaluations)
        assert result.n_flagged == 1
        assert result.n_false_positive == 1
        assert result.all_noise is True


class TestCompareReports:
    """Tests for compare_reports edge cases."""

    def _make_report(self, targets: list[QualityTarget]) -> BenchmarkReport:
        return BenchmarkReport(targets=tuple(targets))

    def test_no_alerts_identical(self) -> None:
        t = QualityTarget("sc_001", "desc", 600.0, 500.0, "higher_is_better")
        report = self._make_report([t])
        alerts = compare_reports(report, report)
        assert alerts == []

    def test_target_regression_detected(self) -> None:
        baseline_t = QualityTarget("sc_001", "desc", 600.0, 500.0, "higher_is_better")
        current_t = QualityTarget("sc_001", "desc", 400.0, 500.0, "higher_is_better")
        baseline = self._make_report([baseline_t])
        current = self._make_report([current_t])
        alerts = compare_reports(current, baseline)
        assert len(alerts) == 1
        assert "regressed" in alerts[0].message

    def test_metric_regression_higher_is_better(self) -> None:
        """Value drops by >10% but target still met."""
        baseline_t = QualityTarget("sc_001", "desc", 1000.0, 500.0, "higher_is_better")
        current_t = QualityTarget("sc_001", "desc", 800.0, 500.0, "higher_is_better")
        baseline = self._make_report([baseline_t])
        current = self._make_report([current_t])
        alerts = compare_reports(current, baseline)
        # 20% regression flagged
        assert len(alerts) == 1
        assert "regressed by" in alerts[0].message

    def test_metric_regression_lower_is_better(self) -> None:
        baseline_t = QualityTarget("sc_004", "desc", 0.10, 0.20, "lower_is_better")
        current_t = QualityTarget("sc_004", "desc", 0.15, 0.20, "lower_is_better")
        baseline = self._make_report([baseline_t])
        current = self._make_report([current_t])
        alerts = compare_reports(current, baseline)
        # 50% increase flagged
        assert len(alerts) == 1
        assert "regressed by" in alerts[0].message

    def test_regression_change_helper_lower_is_better(self) -> None:
        baseline_t = QualityTarget("sc_004", "desc", 0.10, 0.20, "lower_is_better")
        current_t = QualityTarget("sc_004", "desc", 0.15, 0.20, "lower_is_better")
        assert _regression_change(current_t, baseline_t) == pytest.approx(0.5)

    def test_no_regression_under_10pct(self) -> None:
        baseline_t = QualityTarget("sc_001", "desc", 1000.0, 500.0, "higher_is_better")
        current_t = QualityTarget("sc_001", "desc", 950.0, 500.0, "higher_is_better")
        baseline = self._make_report([baseline_t])
        current = self._make_report([current_t])
        alerts = compare_reports(current, baseline)
        assert alerts == []  # only 5% drop

    def test_new_target_not_in_baseline_ignored(self) -> None:
        baseline_t = QualityTarget("sc_001", "desc", 600.0, 500.0, "higher_is_better")
        current_t = QualityTarget("sc_new", "desc", 10.0, 100.0, "higher_is_better")
        baseline = self._make_report([baseline_t])
        current = self._make_report([current_t])
        alerts = compare_reports(current, baseline)
        assert alerts == []

    def test_none_baseline_no_regression(self) -> None:
        baseline_t = QualityTarget("sc_001", "desc", None, 500.0, "higher_is_better")
        current_t = QualityTarget("sc_001", "desc", None, 500.0, "higher_is_better")
        baseline = self._make_report([baseline_t])
        current = self._make_report([current_t])
        alerts = compare_reports(current, baseline)
        assert alerts == []

    def test_zero_baseline_no_division_error(self) -> None:
        baseline_t = QualityTarget("sc_001", "desc", 0.0, 500.0, "higher_is_better")
        current_t = QualityTarget("sc_001", "desc", 0.0, 500.0, "higher_is_better")
        baseline = self._make_report([baseline_t])
        current = self._make_report([current_t])
        alerts = compare_reports(current, baseline)
        # No division by zero
        assert alerts == []


class TestUseCaseBenchmarkTargets:
    """Tests for _compute_targets (SC-001, SC-002, SC-003)."""

    def test_sc003_no_dim_disc(self) -> None:
        """SC-003 with dim_disc=None should produce impl_strong=0."""
        helm = MagicMock()
        bench = UseCaseBenchmark(helm=helm)
        targets = bench._compute_targets([], [], dim_disc=None)
        sc003 = next(t for t in targets if t.name == "sc_003_dimension_discrimination")
        assert sc003.baseline == 0.0

    def test_sc002_no_init_category(self) -> None:
        """SC-002 gap is None when no init category is present."""
        helm = MagicMock()
        bench = UseCaseBenchmark(helm=helm)
        impl_dist = CategoryDistribution(
            FileCategory.IMPLEMENTATION, 10, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7
        )
        targets = bench._compute_targets([], [impl_dist])
        sc002 = next(t for t in targets if t.name == "sc_002_impl_vs_init_gap")
        assert sc002.baseline is None

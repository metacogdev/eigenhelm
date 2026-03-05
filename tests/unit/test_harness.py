"""Unit tests for harness — CorpusStats, HarnessReport, runner.

pytestmark = pytest.mark.contract
"""

from __future__ import annotations

import pytest
from eigenhelm.harness.report import CorpusStats, HarnessReport

pytestmark = pytest.mark.contract


class TestCorpusStats:
    def test_fields_from_known_input(self):
        stats = CorpusStats(
            n_files=3,
            n_skipped=0,
            mean_score=0.4,
            median_score=0.35,
            std_score=0.1,
            accepted=1,
            warned=1,
            rejected=1,
            scores=(0.3, 0.35, 0.55),
        )
        assert stats.n_files == 3
        assert stats.mean_score == 0.4
        assert stats.scores == (0.3, 0.35, 0.55)

    def test_frozen(self):
        stats = CorpusStats(
            n_files=1,
            n_skipped=0,
            mean_score=0.5,
            median_score=0.5,
            std_score=0.0,
            accepted=1,
            warned=0,
            rejected=0,
            scores=(0.5,),
        )
        with pytest.raises(AttributeError):
            stats.n_files = 2  # type: ignore[misc]


class TestHarnessReport:
    def test_delta_sign_convention(self):
        """Negative delta = improvement."""
        before = CorpusStats(
            n_files=5,
            n_skipped=0,
            mean_score=0.6,
            median_score=0.6,
            std_score=0.1,
            accepted=0,
            warned=2,
            rejected=3,
            scores=(0.5, 0.55, 0.6, 0.65, 0.7),
        )
        after = CorpusStats(
            n_files=5,
            n_skipped=0,
            mean_score=0.3,
            median_score=0.3,
            std_score=0.05,
            accepted=4,
            warned=1,
            rejected=0,
            scores=(0.25, 0.28, 0.3, 0.32, 0.35),
        )
        report = HarnessReport(
            before=before,
            after=after,
            delta_mean_score=-0.3,
            u_statistic=0.0,
            p_value=0.008,
            significant=True,
            improvement=True,
        )
        assert report.delta_mean_score < 0
        assert report.improvement is True


class TestRunCorpus:
    def test_empty_directory_raises(self, tmp_path):
        """run_corpus raises ValueError on empty directory."""
        from eigenhelm.harness.runner import run_corpus
        from eigenhelm.helm import DynamicHelm

        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        helm = DynamicHelm()
        with pytest.raises(ValueError, match="No eligible"):
            run_corpus(empty_dir, helm)


class TestRunHarness:
    def test_identical_distributions_not_significant(self, tmp_path):
        """Identical samples → significant is False."""
        import pathlib

        from eigenhelm.harness.runner import run_harness

        dir_a = tmp_path / "a"
        dir_a.mkdir()
        dir_b = tmp_path / "b"
        dir_b.mkdir()

        # Copy fixture files to both dirs — same content → same scores
        fixtures = pathlib.Path(__file__).parent.parent / "fixtures"
        for src_file in sorted(fixtures.iterdir()):
            if src_file.is_file():
                (dir_a / src_file.name).write_bytes(src_file.read_bytes())
                (dir_b / src_file.name).write_bytes(src_file.read_bytes())

        report = run_harness(dir_a, dir_b)
        # Identical distributions: Mann-Whitney U should not find significance
        assert abs(report.delta_mean_score) < 1e-10
        assert report.significant is False

    def test_distinct_distributions_significant(self, tmp_path):
        """Clearly different corpora → significant and improvement."""
        from eigenhelm.harness.runner import run_harness

        before_dir = tmp_path / "before"
        before_dir.mkdir()
        after_dir = tmp_path / "after"
        after_dir.mkdir()

        # Before: structured code with higher aesthetic loss
        complex_code = (
            "def quicksort(arr):\n"
            "    if len(arr) <= 1:\n"
            "        return arr\n"
            "    pivot = arr[0]\n"
            "    left = [x for x in arr[1:] if x < pivot]\n"
            "    right = [x for x in arr[1:] if x >= pivot]\n"
            "    return quicksort(left) + [pivot] + quicksort(right)\n"
        )
        for i in range(10):
            (before_dir / f"complex_{i}.py").write_text(complex_code)

        # After: simple code with lower aesthetic loss
        for i in range(10):
            (after_dir / f"simple_{i}.py").write_text(f"x_{i} = 1\n" * 50)

        report = run_harness(before_dir, after_dir)
        assert report.significant is True
        assert report.improvement is True
        assert report.delta_mean_score < 0

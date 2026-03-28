"""Integration test for the evaluation harness pipeline."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration


class TestHarnessPipeline:
    """SC-004: Harness correctly discriminates known-good from known-bad code."""

    def test_high_vs_low_scoring_corpus(self, tmp_path):
        """Worse corpus (before) vs better corpus (after) → improvement detected.

        With corrected polarity (013): repetitive code scores higher (worse),
        structured code scores lower (better).
        """
        from eigenhelm.harness.runner import run_harness

        before_dir = tmp_path / "before"
        before_dir.mkdir()
        after_dir = tmp_path / "after"
        after_dir.mkdir()

        # Before: repetitive code scores higher (worse) with corrected polarity
        for i in range(10):
            (before_dir / f"simple_{i}.py").write_text(f"x_{i} = 1\n" * 50)

        # After: structured quicksort code scores lower (better) with corrected polarity
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
            (after_dir / f"complex_{i}.py").write_text(complex_code)

        report = run_harness(before_dir, after_dir)

        # SC-004: delta_mean_score < 0 (improvement — after scores lower)
        assert report.delta_mean_score < 0
        assert report.significant is True
        assert report.improvement is True
        # Verify invariant 18 consistency
        assert report.significant == (report.p_value < 0.05)
        assert report.improvement == (
            report.significant and report.delta_mean_score < 0.0
        )

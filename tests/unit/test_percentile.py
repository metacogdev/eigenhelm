"""Unit tests for eigenhelm.output.percentile — percentile computation and ranking."""

from __future__ import annotations

import pytest

from eigenhelm.models import ScoreDistribution
from eigenhelm.output.percentile import (
    compute_quality_percentile,
    compute_ranking,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_dist(
    *,
    min_: float = 0.20,
    p10: float = 0.30,
    p25: float = 0.40,
    median: float = 0.50,
    p75: float = 0.60,
    p90: float = 0.70,
    max_: float = 0.80,
    n_scores: int = 100,
) -> ScoreDistribution:
    return ScoreDistribution(
        min=min_,
        p10=p10,
        p25=p25,
        median=median,
        p75=p75,
        p90=p90,
        max=max_,
        n_scores=n_scores,
    )


# ---------------------------------------------------------------------------
# compute_quality_percentile tests
# ---------------------------------------------------------------------------


class TestComputeQualityPercentile:
    def test_none_distribution_returns_unavailable(self) -> None:
        result = compute_quality_percentile(0.5, None)
        assert result.available is False
        assert result.percentile == 0.0
        assert result.raw_loss_percentile == 0.0

    def test_exact_minimum_returns_quality_100(self) -> None:
        dist = _make_dist()
        result = compute_quality_percentile(0.20, dist)
        assert result.available is True
        assert result.percentile == pytest.approx(100.0)
        assert result.raw_loss_percentile == pytest.approx(0.0)

    def test_exact_maximum_returns_quality_0(self) -> None:
        dist = _make_dist()
        result = compute_quality_percentile(0.80, dist)
        assert result.available is True
        assert result.percentile == pytest.approx(0.0)
        assert result.raw_loss_percentile == pytest.approx(100.0)

    def test_exact_median_returns_quality_50(self) -> None:
        dist = _make_dist()
        result = compute_quality_percentile(0.50, dist)
        assert result.available is True
        assert result.percentile == pytest.approx(50.0)
        assert result.raw_loss_percentile == pytest.approx(50.0)

    def test_clamp_below_min(self) -> None:
        dist = _make_dist()
        result = compute_quality_percentile(0.10, dist)
        assert result.available is True
        assert result.percentile == pytest.approx(100.0)
        assert result.raw_loss_percentile == pytest.approx(0.0)

    def test_clamp_above_max(self) -> None:
        dist = _make_dist()
        result = compute_quality_percentile(0.90, dist)
        assert result.available is True
        assert result.percentile == pytest.approx(0.0)
        assert result.raw_loss_percentile == pytest.approx(100.0)

    def test_interpolation_between_p25_and_median(self) -> None:
        dist = _make_dist()
        # Midpoint between p25 (0.40) and median (0.50) → loss percentile 37.5
        result = compute_quality_percentile(0.45, dist)
        assert result.available is True
        assert result.raw_loss_percentile == pytest.approx(37.5)
        assert result.percentile == pytest.approx(62.5)

    def test_quality_percentile_inverts_loss(self) -> None:
        dist = _make_dist()
        result = compute_quality_percentile(0.30, dist)  # Exactly p10
        assert result.raw_loss_percentile == pytest.approx(10.0)
        assert result.percentile == pytest.approx(90.0)

    def test_near_median_score(self) -> None:
        """Spec US1 scenario 2: score 0.62 with median 0.612 → ~p50."""
        dist = _make_dist(
            min_=0.20,
            p10=0.35,
            p25=0.45,
            median=0.612,
            p75=0.75,
            p90=0.85,
            max_=1.0,
        )
        result = compute_quality_percentile(0.62, dist)
        assert result.available is True
        # Should be near p50 quality (slightly below 50 since 0.62 > 0.612)
        assert 45.0 < result.percentile < 55.0

    def test_flat_distribution_returns_p50(self) -> None:
        """Degenerate distribution (all points equal) → p50 quality."""
        dist = _make_dist(
            min_=0.5, p10=0.5, p25=0.5, median=0.5, p75=0.5, p90=0.5, max_=0.5
        )
        result = compute_quality_percentile(0.5, dist)
        assert result.available is True
        assert result.percentile == pytest.approx(50.0)
        assert result.raw_loss_percentile == pytest.approx(50.0)

    def test_exact_summary_points(self) -> None:
        dist = _make_dist()
        for score, expected_loss_pct in [
            (0.20, 0.0),
            (0.30, 10.0),
            (0.40, 25.0),
            (0.50, 50.0),
            (0.60, 75.0),
            (0.70, 90.0),
            (0.80, 100.0),
        ]:
            result = compute_quality_percentile(score, dist)
            assert result.raw_loss_percentile == pytest.approx(expected_loss_pct), (
                f"score={score}"
            )
            assert result.percentile == pytest.approx(100.0 - expected_loss_pct), (
                f"score={score}"
            )


# ---------------------------------------------------------------------------
# compute_ranking tests
# ---------------------------------------------------------------------------


class TestComputeRanking:
    def test_empty_results(self) -> None:
        ranking = compute_ranking([])
        assert ranking.files == ()
        assert ranking.highlight_count == 0
        assert ranking.spread == 0.0

    def test_single_file_no_highlight(self) -> None:
        ranking = compute_ranking([("a.py", 0.5, 50.0)])
        assert len(ranking.files) == 1
        assert ranking.files[0].rank == 1
        assert ranking.highlight_count == 0

    def test_sort_order_ascending(self) -> None:
        results = [("b.py", 0.8, None), ("a.py", 0.3, None), ("c.py", 0.5, None)]
        ranking = compute_ranking(results)
        assert [f.file_path for f in ranking.files] == ["a.py", "c.py", "b.py"]
        assert [f.rank for f in ranking.files] == [1, 2, 3]

    def test_spread_calculation(self) -> None:
        results = [("a.py", 0.2, None), ("b.py", 0.7, None)]
        ranking = compute_ranking(results)
        assert ranking.spread == pytest.approx(0.5)

    @pytest.mark.parametrize(
        ("count", "expected_highlight"),
        [
            (2, 0),   # floor(2*0.20)=0
            (5, 1),   # floor(5*0.20)=1, min(3,1)=1
            (10, 2),  # floor(10*0.20)=2, min(3,2)=2
            (15, 3),  # floor(15*0.20)=3, min(3,3)=3
            (20, 3),  # floor(20*0.20)=4, min(3,4)=3
        ],
    )
    def test_default_highlight_count(self, count: int, expected_highlight: int) -> None:
        results = [(f"f{i}.py", float(i), None) for i in range(count)]
        ranking = compute_ranking(results)
        assert ranking.highlight_count == expected_highlight

    def test_bottom_override(self) -> None:
        results = [(f"f{i}.py", float(i), None) for i in range(10)]
        ranking = compute_ranking(results, bottom=5)
        assert ranking.highlight_count == 5

    def test_bottom_pct_override(self) -> None:
        results = [(f"f{i}.py", float(i), None) for i in range(10)]
        ranking = compute_ranking(results, bottom_pct=50.0)
        assert ranking.highlight_count == 5

    def test_tie_resolution_at_boundary(self) -> None:
        # 5 files, 3 with score 0.8 (tied at boundary)
        results = [
            ("a.py", 0.3, None),
            ("b.py", 0.5, None),
            ("c.py", 0.8, None),
            ("d.py", 0.8, None),
            ("e.py", 0.8, None),
        ]
        # Default: min(3, floor(5*0.20))=1, but cutoff score = 0.8 ties 3 files
        ranking = compute_ranking(results)
        highlighted = [f for f in ranking.files if f.highlighted]
        assert len(highlighted) == 3  # All three 0.8 files

    def test_all_identical_scores(self) -> None:
        results = [(f"f{i}.py", 0.5, 50.0) for i in range(5)]
        ranking = compute_ranking(results)
        # Spec edge case: all identical scores → no outliers, 0 highlighted
        assert ranking.highlight_count == 0
        assert ranking.spread == pytest.approx(0.0)
        assert all(not f.highlighted for f in ranking.files)

    def test_highlighted_flag_on_bottom_files(self) -> None:
        results = [(f"f{i}.py", float(i), None) for i in range(10)]
        ranking = compute_ranking(results)
        # Default: min(3, floor(10*0.20))=2, bottom 2 are f8.py and f9.py
        for f in ranking.files:
            if f.rank >= 9:  # Bottom 2
                assert f.highlighted is True
            else:
                assert f.highlighted is False

    def test_percentile_preserved(self) -> None:
        results = [("a.py", 0.3, 70.0), ("b.py", 0.8, 20.0)]
        ranking = compute_ranking(results)
        assert ranking.files[0].percentile == 70.0
        assert ranking.files[1].percentile == 20.0

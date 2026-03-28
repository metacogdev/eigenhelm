"""Unit tests for region span derivation (019-test-code-split T012)."""

from __future__ import annotations

from eigenhelm.regions import derive_spans
from eigenhelm.regions.models import RegionSpan, RegionType, TestBoundary


def test_no_boundaries_returns_empty():
    assert derive_spans((), total_lines=100) == ()


def test_single_boundary_at_end():
    boundaries = (
        TestBoundary(
            start_line=81, end_line=100, language="rust", pattern="cfg_test_module"
        ),
    )
    spans = derive_spans(boundaries, total_lines=100)
    assert len(spans) == 2
    assert spans[0] == RegionSpan(
        label=RegionType.PRODUCTION, start_line=1, end_line=80
    )
    assert spans[1] == RegionSpan(label=RegionType.TEST, start_line=81, end_line=100)


def test_single_boundary_at_start():
    """Pure-test file — test code starts at line 1."""
    boundaries = (
        TestBoundary(
            start_line=1, end_line=50, language="python", pattern="test_class"
        ),
    )
    spans = derive_spans(boundaries, total_lines=50)
    assert len(spans) == 1
    assert spans[0].label == RegionType.TEST


def test_single_boundary_mid_file():
    boundaries = (
        TestBoundary(
            start_line=40, end_line=60, language="python", pattern="test_class"
        ),
    )
    spans = derive_spans(boundaries, total_lines=80)
    assert len(spans) == 3
    assert spans[0] == RegionSpan(
        label=RegionType.PRODUCTION, start_line=1, end_line=39
    )
    assert spans[1] == RegionSpan(label=RegionType.TEST, start_line=40, end_line=60)
    assert spans[2] == RegionSpan(
        label=RegionType.PRODUCTION, start_line=61, end_line=80
    )


def test_non_contiguous_test_spans():
    """Python-style interleaved test functions."""
    boundaries = (
        TestBoundary(
            start_line=20, end_line=30, language="python", pattern="test_function"
        ),
        TestBoundary(
            start_line=50, end_line=60, language="python", pattern="test_function"
        ),
    )
    spans = derive_spans(boundaries, total_lines=80)
    assert len(spans) == 5
    assert spans[0] == RegionSpan(
        label=RegionType.PRODUCTION, start_line=1, end_line=19
    )
    assert spans[1] == RegionSpan(label=RegionType.TEST, start_line=20, end_line=30)
    assert spans[2] == RegionSpan(
        label=RegionType.PRODUCTION, start_line=31, end_line=49
    )
    assert spans[3] == RegionSpan(label=RegionType.TEST, start_line=50, end_line=60)
    assert spans[4] == RegionSpan(
        label=RegionType.PRODUCTION, start_line=61, end_line=80
    )


def test_pure_test_file_no_production():
    """File is entirely test code."""
    boundaries = (
        TestBoundary(
            start_line=1, end_line=100, language="rust", pattern="cfg_test_module"
        ),
    )
    spans = derive_spans(boundaries, total_lines=100)
    assert len(spans) == 1
    assert spans[0].label == RegionType.TEST


def test_adjacent_boundaries():
    """Two test regions with no gap between them."""
    boundaries = (
        TestBoundary(
            start_line=1, end_line=10, language="python", pattern="test_class"
        ),
        TestBoundary(
            start_line=11, end_line=20, language="python", pattern="test_class"
        ),
    )
    spans = derive_spans(boundaries, total_lines=30)
    assert len(spans) == 3  # test, test, production trailing
    assert spans[0].label == RegionType.TEST
    assert spans[1].label == RegionType.TEST
    assert spans[2] == RegionSpan(
        label=RegionType.PRODUCTION, start_line=21, end_line=30
    )

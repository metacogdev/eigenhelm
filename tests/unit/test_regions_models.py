"""Unit tests for regions.models — TestBoundary and RegionSpan validation.

Covers: __post_init__ validation (lines 30, 45).
"""

from __future__ import annotations

import pytest

from eigenhelm.regions.models import RegionSpan, RegionType, TestBoundary


class TestTestBoundaryValidation:
    def test_valid_boundary(self):
        b = TestBoundary(start_line=1, end_line=10, language="python", pattern="test_class")
        assert b.start_line == 1
        assert b.end_line == 10

    def test_equal_lines(self):
        b = TestBoundary(start_line=5, end_line=5, language="rust", pattern="cfg_test_module")
        assert b.start_line == b.end_line

    def test_start_after_end_raises(self):
        with pytest.raises(ValueError, match="start_line.*must be <= end_line"):
            TestBoundary(start_line=10, end_line=5, language="python", pattern="test_class")


class TestRegionSpanValidation:
    def test_valid_span(self):
        s = RegionSpan(label=RegionType.PRODUCTION, start_line=1, end_line=50)
        assert s.start_line == 1

    def test_equal_lines(self):
        s = RegionSpan(label=RegionType.TEST, start_line=3, end_line=3)
        assert s.start_line == s.end_line

    def test_start_after_end_raises(self):
        with pytest.raises(ValueError, match="start_line.*must be <= end_line"):
            RegionSpan(label=RegionType.PRODUCTION, start_line=20, end_line=10)

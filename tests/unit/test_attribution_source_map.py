"""Tests for source location mapping (017-score-attribution, T018).

Covers:
  - Structural dims get SourceLocation from CodeUnit
  - Info-theoretic dims get full source SourceLocation
  - stdin → file_path=None
  - Unavailable dims → source_location=None
"""

from __future__ import annotations


from eigenhelm.attribution.models import SourceLocation
from eigenhelm.attribution.source_map import (
    source_location_from_code_unit,
    source_location_from_source,
)
from eigenhelm.models import CodeUnit


class TestSourceLocationFromCodeUnit:
    """source_location_from_code_unit extracts from CodeUnit metadata."""

    def test_extracts_all_fields(self) -> None:
        cu = CodeUnit(
            source="def foo(): pass",
            language="python",
            name="foo",
            start_line=10,
            end_line=15,
            file_path="src/example.py",
        )
        loc = source_location_from_code_unit(cu)

        assert isinstance(loc, SourceLocation)
        assert loc.code_unit_name == "foo"
        assert loc.start_line == 10
        assert loc.end_line == 15
        assert loc.file_path == "src/example.py"

    def test_file_path_none(self) -> None:
        cu = CodeUnit(
            source="def bar(): pass",
            language="python",
            name="bar",
            start_line=1,
            end_line=1,
            file_path=None,
        )
        loc = source_location_from_code_unit(cu)

        assert loc.file_path is None
        assert loc.code_unit_name == "bar"


class TestSourceLocationFromSource:
    """source_location_from_source covers full source for info-theoretic dims."""

    def test_full_source_location(self) -> None:
        source = "line1\nline2\nline3\n"
        loc = source_location_from_source(source, file_path="test.py")

        assert loc.code_unit_name == "<source>"
        assert loc.start_line == 1
        assert loc.end_line == 3
        assert loc.file_path == "test.py"

    def test_single_line(self) -> None:
        loc = source_location_from_source("single line", file_path="x.py")

        assert loc.start_line == 1
        assert loc.end_line == 1

    def test_stdin_no_file_path(self) -> None:
        loc = source_location_from_source("def f(): pass")

        assert loc.file_path is None
        assert loc.code_unit_name == "<source>"
        assert loc.start_line == 1

    def test_empty_source(self) -> None:
        loc = source_location_from_source("")

        assert loc.start_line == 1
        assert loc.end_line == 1

    def test_trailing_newline_not_counted(self) -> None:
        """'a\\nb\\n' has 2 lines, not 3."""
        loc = source_location_from_source("a\nb\n")

        assert loc.end_line == 2

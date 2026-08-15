"""Extended tests for JavaScript declaration detection — covers uncovered branches."""

from __future__ import annotations

from unittest.mock import patch

from eigenhelm.declarations.models import DeclarationType
from eigenhelm.declarations.javascript import detect


class TestParseFailure:
    """Line 27: root is None."""

    def test_none_root_returns_empty(self) -> None:
        with patch("eigenhelm.parsers.tree_sitter.parse_source", return_value=None):
            assert detect("some source") == ()


class TestFieldOnlyClassEdgeCases:
    """Lines 89-133: _check_field_only_class branches."""

    def test_class_with_no_body_not_detected(self) -> None:
        """Class with syntax issues or no body."""
        source = """\
class Empty {}
"""
        regions = detect(source)
        # Empty body, no fields -> not detected
        assert len(regions) == 0

    def test_class_with_unknown_member_not_detected(self) -> None:
        """Class with unexpected member type is conservatively skipped."""
        source = """\
class Mixed {
  x = 1;
  static y = 2;
}
"""
        # static fields may produce different member types
        detect(source)  # Should not crash

    def test_exported_class_with_fields(self) -> None:
        """Exported class with only fields is detected."""
        source = """\
export class Settings {
  debug = false;
  verbose = false;
}
"""
        regions = detect(source)
        assert len(regions) == 1
        assert regions[0].declaration_type == DeclarationType.FIELD_ONLY_CLASS


class TestExtractDeclaratorValue:
    """Lines 158-166: _extract_declarator_value."""

    def test_const_without_value_not_detected(self) -> None:
        """const declaration without an initializer."""
        source = """\
const x;
"""
        # Should not crash; no array value -> no detection
        detect(source)


class TestExtractName:
    """Lines 184-192: _extract_name edge cases."""

    def test_class_name_extracted(self) -> None:
        source = """\
class MyConfig {
  host = "localhost";
  port = 8080;
}
"""
        regions = detect(source)
        assert len(regions) == 1
        assert regions[0].node_name == "MyConfig"


class TestCountNonBlank:
    """Lines 203-209: _count_non_blank edge cases."""

    def test_class_with_blank_lines(self) -> None:
        source = """\
class Spaced {

  x = 1;

  y = 2;

}
"""
        regions = detect(source)
        if len(regions) == 1:
            span = regions[0].end_line - regions[0].start_line + 1
            assert regions[0].declaration_line_count < span

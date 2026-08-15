"""Unit tests for parsers.tree_sitter — parse_source, extract_units, extract_units_partial.

Covers: error handling, unsupported language, empty/whitespace input,
fallback paths, and partial parse with syntax errors.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from eigenhelm.models import UnsupportedLanguageError
from eigenhelm.parsers.tree_sitter import (
    extract_units,
    extract_units_partial,
    parse_source,
)


# ---------------------------------------------------------------------------
# parse_source
# ---------------------------------------------------------------------------


class TestParseSource:
    def test_unsupported_language(self):
        with pytest.raises(UnsupportedLanguageError):
            parse_source("x = 1", "brainfuck")

    def test_valid_python(self):
        root = parse_source("x = 1\n", "python")
        assert root is not None
        assert root.type == "module"

    def test_returns_none_when_tree_sitter_missing(self):
        with patch("eigenhelm.parsers.tree_sitter._HAS_TREE_SITTER", False):
            result = parse_source("x = 1", "python")
        assert result is None

    def test_unsupported_before_tree_sitter_check(self):
        """UnsupportedLanguageError raised even if tree-sitter is missing."""
        with patch("eigenhelm.parsers.tree_sitter._HAS_TREE_SITTER", False):
            with pytest.raises(UnsupportedLanguageError):
                parse_source("x = 1", "brainfuck")


# ---------------------------------------------------------------------------
# extract_units
# ---------------------------------------------------------------------------


class TestExtractUnits:
    def test_empty_source(self):
        assert extract_units("", "python") == []

    def test_whitespace_only(self):
        assert extract_units("   \n\t\n  ", "python") == []

    def test_unsupported_language(self):
        with pytest.raises(UnsupportedLanguageError):
            extract_units("x = 1", "brainfuck")

    def test_single_function(self):
        source = """\
def foo():
    return 42
"""
        units = extract_units(source, "python")
        assert len(units) == 1
        assert units[0].name == "foo"
        assert units[0].language == "python"

    def test_no_named_units_falls_back(self):
        """Source with no function/class defs falls back to single module unit."""
        source = "x = 1\ny = 2\n"
        units = extract_units(source, "python")
        assert len(units) == 1
        assert units[0].name == "<module>"

    def test_file_path_annotation(self):
        source = "def bar(): pass\n"
        units = extract_units(source, "python", file_path="/tmp/bar.py")
        assert units[0].file_path == "/tmp/bar.py"

    def test_fallback_when_tree_sitter_unavailable(self):
        source = "def hello(): pass\n"
        with patch("eigenhelm.parsers.tree_sitter._HAS_TREE_SITTER", False):
            units = extract_units(source, "python")
        assert len(units) == 1
        assert units[0].name == "<module>"

    def test_multiple_functions(self):
        source = """\
def foo():
    return 1

def bar():
    return 2

class Baz:
    def method(self):
        pass
"""
        units = extract_units(source, "python")
        names = {u.name for u in units}
        assert "foo" in names
        assert "bar" in names
        assert "Baz" in names


# ---------------------------------------------------------------------------
# extract_units_partial
# ---------------------------------------------------------------------------


class TestExtractUnitsPartial:
    def test_unsupported_language(self):
        units, partial = extract_units_partial("x = 1", "brainfuck")
        assert units == []
        assert partial is False

    def test_valid_python_no_errors(self):
        source = "def foo(): return 1\n"
        units, partial = extract_units_partial(source, "python")
        assert len(units) == 1
        assert partial is False

    def test_syntax_error_detected(self):
        """Malformed code should set partial=True."""
        source = "def foo(:\n    pass\n"
        units, partial = extract_units_partial(source, "python")
        # Should still return something (fallback or partial units)
        assert isinstance(units, list)
        assert partial is True

    def test_fallback_when_tree_sitter_unavailable(self):
        source = "def hello(): pass\n"
        with patch("eigenhelm.parsers.tree_sitter._HAS_TREE_SITTER", False):
            units, partial = extract_units_partial(source, "python")
        assert len(units) == 1
        assert units[0].name == "<module>"
        assert partial is False

    def test_no_named_units_falls_back(self):
        source = "x = 1\n"
        units, partial = extract_units_partial(source, "python")
        assert len(units) == 1
        assert units[0].name == "<module>"

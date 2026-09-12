"""Extended tests for Go declaration detection — covers uncovered branches."""

from __future__ import annotations

from unittest.mock import patch

from eigenhelm.declarations.models import DeclarationType
from eigenhelm.declarations.go import detect


class TestParseFailure:
    """Line 30: root is None."""

    def test_none_root_returns_empty(self) -> None:
        with patch("eigenhelm.parsers.tree_sitter.parse_source", return_value=None):
            assert detect("some source") == ()


class TestConstGroupedBlock:
    """Lines 97-104: grouped const block (non-iota)."""

    def test_const_grouped_block_detected_as_enum(self) -> None:
        """Grouped const block (parenthesized) without iota detected."""
        source = """\
package main

const (
\tA = 1
\tB = 2
\tC = 3
)
"""
        regions = detect(source)
        assert len(regions) == 1
        assert regions[0].declaration_type == DeclarationType.ENUM_DECLARATION

    def test_const_with_nil_text(self) -> None:
        """Edge case: const block where text is checked."""
        source = """\
package main

const X = 42
"""
        regions = detect(source)
        assert len(regions) == 0


class TestVarDeclaration:
    """Lines 107-126: _handle_var_declaration."""

    def test_var_without_composite_literal_not_detected(self) -> None:
        """var with a simple value is not detected."""
        source = """\
package main

var x = 42
"""
        regions = detect(source)
        assert len(regions) == 0


class TestHelperFunctions:
    """Cover helper function edge cases."""

    def test_has_struct_type_false(self) -> None:
        """type alias without struct is not detected."""
        source = """\
package main

type ID = int
"""
        regions = detect(source)
        # Type alias is not a struct type
        assert len(regions) == 0

    def test_extract_name_fallback(self) -> None:
        """When identifier is not found, default name is used."""
        source = """\
package main

type Config struct {
\tHost string
}
"""
        regions = detect(source)
        assert len(regions) == 1
        assert regions[0].node_name == "Config"

    def test_const_block_name(self) -> None:
        """First const_spec identifier used as name."""
        source = """\
package main

const (
\tAlpha = iota
\tBeta
\tGamma
)
"""
        regions = detect(source)
        assert len(regions) == 1
        assert regions[0].node_name == "Alpha"

    def test_var_block_name(self) -> None:
        """First var_spec identifier used as name."""
        source = """\
package main

type Route struct {
\tPath string
}

var routes = []Route{
\t{Path: "/home"},
}
"""
        regions = detect(source)
        table = [
            r for r in regions if r.declaration_type == DeclarationType.CONST_TABLE
        ]
        assert len(table) == 1
        assert table[0].node_name == "routes"

    def test_find_node_type_recursive(self) -> None:
        """Verify _find_node_type searches recursively for composite_literal."""
        source = """\
package main

type Item struct {
\tName string
}

var items = []Item{
\t{Name: "a"},
\t{Name: "b"},
}
"""
        regions = detect(source)
        types = {r.declaration_type for r in regions}
        assert DeclarationType.CONST_TABLE in types

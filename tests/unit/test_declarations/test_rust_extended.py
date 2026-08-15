"""Extended tests for Rust declaration detection — covers uncovered branches."""

from __future__ import annotations

import textwrap
from unittest.mock import patch

from eigenhelm.declarations.models import DeclarationType
from eigenhelm.declarations.rust import detect


class TestParseFailure:
    """Line 28: root is None when parse fails."""

    def test_none_root_returns_empty(self) -> None:
        with patch("eigenhelm.parsers.tree_sitter.parse_source", return_value=None):
            assert detect("some source") == ()


class TestConstTableRefExpression:
    """Lines 57-61: reference_expression wrapping array_expression."""

    def test_static_ref_array_of_structs(self) -> None:
        """static with &[Struct{...}] reference expression detected."""
        src = textwrap.dedent("""\
            static ITEMS: &[Item] = &[
                Item { name: "a", val: 1 },
                Item { name: "b", val: 2 },
            ];
        """)
        regions = detect(src)
        assert len(regions) == 1
        assert regions[0].declaration_type == DeclarationType.CONST_TABLE

    def test_const_array_no_struct_not_detected(self) -> None:
        """const array without struct expressions is not detected."""
        src = textwrap.dedent("""\
            const NUMS: [i32; 3] = [1, 2, 3];
        """)
        regions = detect(src)
        assert len(regions) == 0

    def test_const_non_array_not_detected(self) -> None:
        """const with non-array value is not detected."""
        src = textwrap.dedent("""\
            const MAX: usize = 100;
        """)
        regions = detect(src)
        assert len(regions) == 0


class TestEnumWithStructVariant:
    """Lines 83-98: enum with struct data variants."""

    def test_enum_with_struct_variant_not_detected(self) -> None:
        """Enum with struct-style data variant is NOT detected."""
        src = textwrap.dedent("""\
            enum Message {
                Quit,
                Move { x: i32, y: i32 },
                Write(String),
            }
        """)
        regions = detect(src)
        assert len(regions) == 0

    def test_enum_no_variant_list_not_detected(self) -> None:
        """Edge case: enum without a variant list body."""
        src = textwrap.dedent("""\
            enum Empty;
        """)
        # Should not crash
        detect(src)


class TestExtractNameFallback:
    """Lines 132-139: _extract_name fallback."""

    def test_struct_name_extracted(self) -> None:
        src = textwrap.dedent("""\
            struct MyConfig {
                field: String,
            }
        """)
        regions = detect(src)
        assert len(regions) == 1
        assert regions[0].node_name == "MyConfig"


class TestCountNonBlankLines:
    """Lines 150-158: _count_non_blank_lines edge cases."""

    def test_struct_with_blank_lines(self) -> None:
        src = textwrap.dedent("""\
            struct Spaced {

                x: f64,

                y: f64,

            }
        """)
        regions = detect(src)
        assert len(regions) == 1
        # Non-blank count should be less than span
        span = regions[0].end_line - regions[0].start_line + 1
        assert regions[0].declaration_line_count < span

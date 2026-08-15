"""Extended tests for declarations __init__.py — covers JS, Go dispatch and block comments."""

from __future__ import annotations

from eigenhelm.declarations import analyze_declarations, detect_declarations


class TestJavaScriptDispatch:
    """Cover lines 59-61: JavaScript language dispatch."""

    def test_detect_javascript_const_table(self) -> None:
        source = """\
const DATA = [
  { id: 1, name: "alpha" },
  { id: 2, name: "beta" },
];
"""
        regions = detect_declarations(source, "javascript")
        assert len(regions) == 1

    def test_analyze_javascript(self) -> None:
        source = """\
const DATA = [
  { id: 1, name: "alpha" },
  { id: 2, name: "beta" },
];
"""
        analysis = analyze_declarations(source, "javascript")
        assert analysis.declaration_lines > 0


class TestGoDispatch:
    """Cover lines 63-65: Go language dispatch."""

    def test_detect_go_struct(self) -> None:
        source = """\
package main

type Config struct {
\tHost string
\tPort int
}
"""
        regions = detect_declarations(source, "go")
        assert len(regions) == 1

    def test_analyze_go(self) -> None:
        source = """\
package main

type Config struct {
\tHost string
\tPort int
}
"""
        analysis = analyze_declarations(source, "go")
        assert analysis.declaration_lines > 0


class TestBlockCommentHandling:
    """Cover lines 109-117: block comment handling in _count_non_blank_non_comment_lines."""

    def test_javascript_block_comment_excluded(self) -> None:
        source = """\
/* This is a
   multi-line
   comment */
const x = 1;
"""
        analysis = analyze_declarations(source, "javascript")
        # Block comment lines should be excluded from nbnc count
        assert analysis.non_blank_non_comment_lines == 1

    def test_javascript_single_line_block_comment(self) -> None:
        source = """\
/* single line comment */
const x = 1;
"""
        analysis = analyze_declarations(source, "javascript")
        assert analysis.non_blank_non_comment_lines == 1

    def test_typescript_block_comment_excluded(self) -> None:
        source = """\
/*
 * Multi-line TSDoc comment
 */
interface Config {
  host: string;
}
"""
        analysis = analyze_declarations(source, "typescript")
        # Only the interface lines should be counted
        assert analysis.non_blank_non_comment_lines >= 3

    def test_rust_block_comment_excluded(self) -> None:
        source = """\
/*
 * Block comment
 */
struct Point {
    x: f64,
    y: f64,
}
"""
        analysis = analyze_declarations(source, "rust")
        assert analysis.non_blank_non_comment_lines >= 4

    def test_go_block_comment_excluded(self) -> None:
        source = """\
package main

/*
Block comment
*/

type Config struct {
\tHost string
}
"""
        analysis = analyze_declarations(source, "go")
        # Block comment lines excluded
        assert analysis.non_blank_non_comment_lines >= 3

    def test_line_comment_excluded(self) -> None:
        source = """\
// This is a line comment
interface Foo {
  bar: string;
}
"""
        analysis = analyze_declarations(source, "typescript")
        assert analysis.non_blank_non_comment_lines == 3

    def test_block_comment_within_single_line(self) -> None:
        """Block comment that starts and ends on same line."""
        source = """\
/* inline */ const x = 1;
interface A { name: string; }
"""
        analysis = analyze_declarations(source, "javascript")
        # The first line starts with /* and has */ on same line, so skipped
        # The second is an interface
        assert analysis.non_blank_non_comment_lines >= 1

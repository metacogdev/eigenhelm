"""Extended tests for barrel file detection — covers uncovered branches."""

from __future__ import annotations

from eigenhelm.declarations.barrel import is_barrel_file


class TestPythonBarrelEdgeCases:
    """Cover missing lines in _is_python_import."""

    def test_comment_lines_counted_as_import(self) -> None:
        """Comment-only file with imports is a barrel."""
        source = """
# Module imports
import os
import sys
import json
# End of imports
"""
        assert is_barrel_file(source, "python") is True

    def test_continuation_line_not_logic(self) -> None:
        """Lines that look like identifier continuations."""
        source = """
from foo import (
    Bar,
    Baz,
    Qux,
)
"""
        assert is_barrel_file(source, "python") is True


class TestRustBarrelEdgeCases:
    """Cover missing lines in _is_rust_use."""

    def test_rust_closing_braces(self) -> None:
        """Closing braces count as import continuation."""
        source = """
use std::io;
use std::fs;
pub use crate::models;
pub mod handlers;
pub mod routes;
"""
        assert is_barrel_file(source, "rust") is True

    def test_rust_continuation_lines(self) -> None:
        """Indented continuation lines in use statements."""
        source = """
pub use crate::one;
pub use crate::two;
pub use crate::three;
pub use crate::four;
pub use crate::five;
"""
        assert is_barrel_file(source, "rust") is True

    def test_rust_comments_counted(self) -> None:
        """Rust comment lines are counted."""
        source = """
// Re-exports
pub use models::Config;
pub use models::State;
pub mod handlers;
pub mod routes;
"""
        assert is_barrel_file(source, "rust") is True

    def test_rust_with_fn_logic_not_barrel(self) -> None:
        """Rust file with fn is not a barrel."""
        source = """
pub use crate::one;

pub fn main() {
    let x = 1;
    let y = 2;
    println!("{}", x + y);
}
"""
        assert is_barrel_file(source, "rust") is False


class TestJsTsBarrelEdgeCases:
    """Cover missing lines in _is_js_ts_import."""

    def test_js_closing_braces(self) -> None:
        """Closing braces in JS count as import."""
        source = """
export { Foo } from "./foo";
export { Bar } from "./bar";
export { Baz } from "./baz";
export { Qux } from "./qux";
export { Quux } from "./quux";
"""
        assert is_barrel_file(source, "javascript") is True

    def test_js_comment_lines_counted(self) -> None:
        """JS comment lines are counted."""
        source = """
// Barrel file
export { A } from "./a";
export { B } from "./b";
export { C } from "./c";
export { D } from "./d";
"""
        assert is_barrel_file(source, "javascript") is True

    def test_js_continuation_indented(self) -> None:
        """Indented continuation lines in JS imports."""
        source = """
import { Foo } from "./foo";
import { Bar } from "./bar";
import { Baz } from "./baz";
export { Foo };
export { Bar };
"""
        assert is_barrel_file(source, "javascript") is True

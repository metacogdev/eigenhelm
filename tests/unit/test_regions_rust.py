"""Unit tests for Rust test boundary detection (eigenhelm.regions.rust).

Covers: cfg(test) module detection, parse failure, false positive avoidance.
"""

from __future__ import annotations

from eigenhelm.regions.rust import detect


class TestDetectBasic:
    def test_empty_source(self):
        assert detect("") == ()

    def test_no_test_module(self):
        source = """\
pub fn add(a: i32, b: i32) -> i32 {
    a + b
}

mod helpers {
    pub fn square(x: i32) -> i32 {
        x * x
    }
}
"""
        assert detect(source) == ()

    def test_cfg_test_module(self):
        source = """\
pub fn add(a: i32, b: i32) -> i32 {
    a + b
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_add() {
        assert_eq!(add(1, 2), 3);
    }
}
"""
        result = detect(source)
        assert len(result) == 1
        assert result[0].pattern == "cfg_test_module"
        assert result[0].language == "rust"

    def test_multiple_test_modules(self):
        source = """\
pub fn foo() -> i32 { 1 }

#[cfg(test)]
mod tests_a {
    #[test]
    fn test_foo() { assert_eq!(super::foo(), 1); }
}

pub fn bar() -> i32 { 2 }

#[cfg(test)]
mod tests_b {
    #[test]
    fn test_bar() { assert_eq!(super::bar(), 2); }
}
"""
        result = detect(source)
        assert len(result) == 2


class TestCfgTestFalsePositives:
    """Cover lines 61-63 and 74: avoid false positives."""

    def test_cfg_not_test_not_detected(self):
        source = """\
#[cfg(not(test))]
mod production_only {
    pub fn secret() -> i32 { 42 }
}
"""
        assert detect(source) == ()

    def test_cfg_feature_not_detected(self):
        source = """\
#[cfg(feature = "contest")]
mod contest {
    pub fn run() {}
}
"""
        assert detect(source) == ()

    def test_plain_mod_not_detected(self):
        """A mod without any cfg attribute should not be detected."""
        source = """\
mod utils {
    pub fn helper() -> bool { true }
}
"""
        assert detect(source) == ()


class TestParseFailure:
    """Cover line 24: parse_source returns None."""

    def test_returns_empty_on_parse_failure(self):
        from eigenhelm.parsers import tree_sitter
        orig = tree_sitter.parse_source
        tree_sitter.parse_source = lambda *a, **k: None
        try:
            result = detect("fn main() {}")
        finally:
            tree_sitter.parse_source = orig
        assert result == ()


class TestAttrTextNone:
    """Cover line 74: attr_node.text is None."""

    def test_none_text_attribute(self):
        from unittest.mock import MagicMock
        from eigenhelm.regions.rust import _is_cfg_test

        node = MagicMock()
        node.text = None
        assert _is_cfg_test(node) is False

    def test_bytes_text_attribute(self):
        from unittest.mock import MagicMock
        from eigenhelm.regions.rust import _is_cfg_test

        node = MagicMock()
        node.text = b"#[cfg(test)]"
        assert _is_cfg_test(node) is True

    def test_string_text_attribute(self):
        from unittest.mock import MagicMock
        from eigenhelm.regions.rust import _is_cfg_test

        node = MagicMock()
        node.text = "#[cfg(test)]"
        assert _is_cfg_test(node) is True

    def test_whitespace_variant(self):
        from unittest.mock import MagicMock
        from eigenhelm.regions.rust import _is_cfg_test

        node = MagicMock()
        node.text = b"#[cfg( test )]"
        assert _is_cfg_test(node) is True


class TestHasCfgTestAttr:
    """Cover line 54 and sibling traversal (lines 57-62)."""

    def test_attr_as_child(self):
        from unittest.mock import MagicMock
        from eigenhelm.regions.rust import _has_cfg_test_attr

        attr = MagicMock()
        attr.type = "attribute_item"
        attr.text = b"#[cfg(test)]"

        mod_node = MagicMock()
        mod_node.children = [attr]
        mod_node.prev_sibling = None

        assert _has_cfg_test_attr(mod_node) is True

    def test_attr_as_preceding_sibling(self):
        from unittest.mock import MagicMock
        from eigenhelm.regions.rust import _has_cfg_test_attr

        attr_sib = MagicMock()
        attr_sib.type = "attribute_item"
        attr_sib.text = b"#[cfg(test)]"
        attr_sib.prev_sibling = None

        mod_node = MagicMock()
        mod_node.children = []
        mod_node.prev_sibling = attr_sib

        assert _has_cfg_test_attr(mod_node) is True

    def test_no_attr_at_all(self):
        from unittest.mock import MagicMock
        from eigenhelm.regions.rust import _has_cfg_test_attr

        mod_node = MagicMock()
        mod_node.children = []
        mod_node.prev_sibling = None

        assert _has_cfg_test_attr(mod_node) is False

    def test_non_cfg_test_sibling_attr(self):
        from unittest.mock import MagicMock
        from eigenhelm.regions.rust import _has_cfg_test_attr

        attr_sib = MagicMock()
        attr_sib.type = "attribute_item"
        attr_sib.text = b"#[derive(Debug)]"
        attr_sib.prev_sibling = None

        mod_node = MagicMock()
        mod_node.children = []
        mod_node.prev_sibling = attr_sib

        assert _has_cfg_test_attr(mod_node) is False

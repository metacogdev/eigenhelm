"""Unit tests for barrel/module-shipping file detection."""

from __future__ import annotations

from eigenhelm.declarations.barrel import is_barrel_file


class TestPythonBarrel:
    def test_pure_init_reexport(self):
        source = """
from eigenhelm.declarations.models import (
    DeclarationAnalysis,
    DeclarationRegion,
    DeclarationType,
)

__all__ = [
    "DeclarationAnalysis",
    "DeclarationRegion",
    "DeclarationType",
]
"""
        assert is_barrel_file(source, "python") is True

    def test_init_with_real_logic(self):
        source = """
from eigenhelm.critic import AestheticCritic

class Foo:
    def __init__(self):
        self.x = 1

    def process(self, data):
        result = []
        for item in data:
            result.append(item * 2)
        return result

def helper():
    return 42
"""
        assert is_barrel_file(source, "python") is False

    def test_mixed_init_below_threshold(self):
        source = """
from foo import Bar
from baz import Qux

def setup():
    return Bar() + Qux()

class Config:
    host: str = "localhost"
    port: int = 8080
"""
        assert is_barrel_file(source, "python") is False

    def test_import_only_file(self):
        source = """
import os
import sys
import json
from pathlib import Path
from typing import Optional
"""
        assert is_barrel_file(source, "python") is True


class TestTypeScriptBarrel:
    def test_pure_reexport_index(self):
        source = """
export { Foo } from "./foo";
export { Bar } from "./bar";
export { Baz } from "./baz";
export { Qux } from "./qux";
export { Quux } from "./quux";
"""
        assert is_barrel_file(source, "typescript") is True

    def test_index_with_logic(self):
        source = """
export { Foo } from "./foo";

export function createApp() {
    const app = new Foo();
    app.init();
    return app;
}
"""
        assert is_barrel_file(source, "typescript") is False


class TestRustBarrel:
    def test_mod_rs_reexports(self):
        source = """
pub mod models;
pub mod python;
pub mod rust;
pub mod typescript;
pub mod javascript;
pub mod go;

pub use models::{DeclarationRegion, DeclarationAnalysis};
"""
        assert is_barrel_file(source, "rust") is True

    def test_mod_rs_with_logic(self):
        source = """
pub mod models;

pub fn detect(source: &str) -> Vec<Region> {
    let mut regions = Vec::new();
    for line in source.lines() {
        if line.starts_with("struct") {
            regions.push(Region::new(line));
        }
    }
    regions
}
"""
        assert is_barrel_file(source, "rust") is False


class TestEdgeCases:
    def test_empty_file(self):
        assert is_barrel_file("", "python") is False

    def test_single_line(self):
        assert is_barrel_file("import os\n", "python") is False

    def test_unsupported_language(self):
        assert is_barrel_file("import foo", "go") is False

    def test_whitespace_only(self):
        assert is_barrel_file("   \n  \n", "python") is False

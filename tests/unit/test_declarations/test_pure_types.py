"""Tests for is_pure_types detection and skip behavior."""

from __future__ import annotations

from eigenhelm.declarations import analyze_declarations


def test_pure_dataclass_file_is_pure_types():
    source = """
from dataclasses import dataclass

@dataclass(frozen=True)
class SearchResult:
    title: str
    url: str
    score: float

@dataclass(frozen=True)
class SearchFilters:
    language: str
    min_score: float
    max_results: int

@dataclass(frozen=True)
class GraphNode:
    id: str
    label: str
    kind: str
"""
    result = analyze_declarations(source, "python")
    assert result.is_dominant is True
    assert result.is_pure_types is True


def test_const_table_file_is_not_pure_types():
    source = """
EVENTS = [
    {"kind": "sunset", "prob": 0.15, "desc": "A beautiful sunset"},
    {"kind": "passage", "prob": 0.10, "desc": "A challenging passage"},
    {"kind": "injury", "prob": 0.05, "desc": "A minor injury"},
    {"kind": "harvest", "prob": 0.08, "desc": "A good harvest"},
    {"kind": "visitor", "prob": 0.12, "desc": "An unexpected visitor"},
]

SEASONS = [
    {"name": "spring", "modifier": 1.2},
    {"name": "summer", "modifier": 0.8},
    {"name": "autumn", "modifier": 1.0},
    {"name": "winter", "modifier": 0.6},
]
"""
    result = analyze_declarations(source, "python")
    # Const tables are not pure types — dampening applies, not skip
    assert result.is_pure_types is False


def test_mixed_types_and_tables_is_not_pure_types():
    source = """
from dataclasses import dataclass

@dataclass(frozen=True)
class Config:
    host: str
    port: int

DEFAULTS = [
    {"host": "localhost", "port": 8080},
    {"host": "0.0.0.0", "port": 9090},
]
"""
    result = analyze_declarations(source, "python")
    # Mixed: has both TYPE_DEFINITION and CONST_TABLE → not pure types
    if result.is_dominant:
        assert result.is_pure_types is False


def test_logic_heavy_file_is_not_pure_types():
    source = """
def process(data):
    for item in data:
        if item > 0:
            print(item)
"""
    result = analyze_declarations(source, "python")
    assert result.is_pure_types is False


def test_typescript_interfaces_are_pure_types():
    source = """
export interface SearchResult {
    title: string;
    url: string;
    score: number;
}

export interface SearchFilters {
    language: string;
    minScore: number;
    maxResults: number;
}

export interface GraphNode {
    id: string;
    label: string;
    kind: string;
}
"""
    result = analyze_declarations(source, "typescript")
    assert result.is_dominant is True
    assert result.is_pure_types is True


def test_rust_structs_are_pure_types():
    source = """
pub struct SearchResult {
    pub title: String,
    pub url: String,
    pub score: f64,
}

pub struct SearchFilters {
    pub language: String,
    pub min_score: f64,
    pub max_results: usize,
}

pub struct GraphNode {
    pub id: String,
    pub label: String,
    pub kind: String,
}
"""
    result = analyze_declarations(source, "rust")
    assert result.is_dominant is True
    assert result.is_pure_types is True


def test_empty_file_is_not_pure_types():
    result = analyze_declarations("", "python")
    assert result.is_pure_types is False

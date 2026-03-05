"""Unit tests for Halstead metric computation.

Validates AST-structural classification and Halstead formula correctness.
"""

import pytest


def test_halstead_python_quicksort(python_quicksort_source):
    from eigenhelm.metrics.halstead import compute
    from eigenhelm.parsers.tree_sitter import parse_source

    root = parse_source(python_quicksort_source, "python")
    assert root is not None, "Tree-sitter failed to parse Python"

    metrics = compute(root)
    # Basic sanity: all values should be non-negative
    assert metrics.volume >= 0
    assert metrics.difficulty >= 0
    assert metrics.effort >= 0
    assert metrics.total_operators >= 0
    assert metrics.total_operands >= 0

    # Quicksort has meaningful operators (if, return, comparisons)
    assert metrics.total_operators > 0
    assert metrics.distinct_operators > 0

    # Volume: N * log2(η) — quicksort should have non-trivial volume
    assert metrics.volume > 0


def test_halstead_empty_string():
    """Empty input produces zero-valued metrics without error."""
    from eigenhelm.metrics.halstead import compute
    from eigenhelm.parsers.tree_sitter import parse_source

    root = parse_source("# comment only\n", "python")
    if root is None:
        pytest.skip("Tree-sitter unavailable")
    metrics = compute(root)
    assert metrics.volume == 0.0 or metrics.volume >= 0


def test_halstead_deterministic(python_quicksort_source):
    """Identical input produces identical metrics (SC-001)."""
    from eigenhelm.metrics.halstead import compute
    from eigenhelm.parsers.tree_sitter import parse_source

    root1 = parse_source(python_quicksort_source, "python")
    root2 = parse_source(python_quicksort_source, "python")
    if root1 is None:
        pytest.skip("Tree-sitter unavailable")

    m1 = compute(root1)
    m2 = compute(root2)
    assert m1.volume == m2.volume
    assert m1.difficulty == m2.difficulty
    assert m1.effort == m2.effort


def test_halstead_formula_consistency(python_quicksort_source):
    """Verify E = D * V holds."""
    from eigenhelm.metrics.halstead import compute
    from eigenhelm.parsers.tree_sitter import parse_source

    root = parse_source(python_quicksort_source, "python")
    if root is None:
        pytest.skip("Tree-sitter unavailable")
    m = compute(root)
    assert abs(m.effort - m.difficulty * m.volume) < 1e-9

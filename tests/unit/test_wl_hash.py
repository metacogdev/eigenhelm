"""Unit tests for WL graph hash histogram computation."""

import numpy as np
import pytest


def test_wl_hash_shape(python_quicksort_source):
    """Output is shape (64,)."""
    from eigenhelm.metrics.wl_hash import compute
    from eigenhelm.parsers.tree_sitter import parse_source

    root = parse_source(python_quicksort_source, "python")
    if root is None:
        pytest.skip("Tree-sitter unavailable")

    hist = compute(root)
    assert hist.shape == (64,)
    assert hist.dtype == np.float64


def test_wl_hash_normalized(python_quicksort_source):
    """Histogram values sum to 1.0 (probability distribution)."""
    from eigenhelm.metrics.wl_hash import compute
    from eigenhelm.parsers.tree_sitter import parse_source

    root = parse_source(python_quicksort_source, "python")
    if root is None:
        pytest.skip("Tree-sitter unavailable")

    hist = compute(root)
    assert pytest.approx(hist.sum(), abs=1e-6) == 1.0


def test_wl_hash_deterministic(python_quicksort_source):
    """Same source → same histogram (SC-001)."""
    from eigenhelm.metrics.wl_hash import compute
    from eigenhelm.parsers.tree_sitter import parse_source

    root1 = parse_source(python_quicksort_source, "python")
    root2 = parse_source(python_quicksort_source, "python")
    if root1 is None:
        pytest.skip("Tree-sitter unavailable")

    h1 = compute(root1)
    h2 = compute(root2)
    np.testing.assert_array_equal(h1, h2)


def test_wl_hash_different_for_different_code():
    """Different code structures produce different histograms."""
    from eigenhelm.metrics.wl_hash import compute
    from eigenhelm.parsers.tree_sitter import parse_source

    src1 = "def foo(x):\n    return x + 1\n"
    src2 = "def bar(x):\n    if x > 0:\n        return x\n    return 0\n"

    r1 = parse_source(src1, "python")
    r2 = parse_source(src2, "python")
    if r1 is None or r2 is None:
        pytest.skip("Tree-sitter unavailable")

    h1 = compute(r1)
    h2 = compute(r2)
    # Histograms should differ (different AST structure)
    assert not np.array_equal(h1, h2)


def test_wl_hash_iteration_cap():
    """Iterations > tree depth saturate without error."""
    from eigenhelm.metrics.wl_hash import compute
    from eigenhelm.parsers.tree_sitter import parse_source

    # Very shallow source
    src = "x = 1\n"
    root = parse_source(src, "python")
    if root is None:
        pytest.skip("Tree-sitter unavailable")

    # Should not raise even with iterations > actual depth
    hist = compute(root, iterations=10)
    assert hist.shape == (64,)


def test_wl_hash_non_negative(python_quicksort_source):
    """All histogram values are >= 0."""
    from eigenhelm.metrics.wl_hash import compute
    from eigenhelm.parsers.tree_sitter import parse_source

    root = parse_source(python_quicksort_source, "python")
    if root is None:
        pytest.skip("Tree-sitter unavailable")

    hist = compute(root)
    assert np.all(hist >= 0)

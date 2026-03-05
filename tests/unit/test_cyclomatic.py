"""Unit tests for Cyclomatic complexity computation via Lizard."""

import pytest


def test_cyclomatic_python_quicksort(python_quicksort_source):
    from eigenhelm.metrics.cyclomatic import compute

    metrics = compute(python_quicksort_source, "python")
    assert metrics.complexity >= 1
    assert metrics.nloc > 0
    assert metrics.density > 0

    # Quicksort has at least 3 branches (if + 2 comprehension conditions)
    assert metrics.complexity >= 2


def test_cyclomatic_simple_function():
    """A straight-line function has cyclomatic complexity of 1."""
    from eigenhelm.metrics.cyclomatic import compute

    source = "def add(a, b):\n    return a + b\n"
    metrics = compute(source, "python")
    assert metrics.complexity == 1
    assert metrics.nloc >= 1
    assert metrics.density == pytest.approx(metrics.complexity / metrics.nloc)


def test_cyclomatic_density_formula(python_quicksort_source):
    """Density = complexity / nloc."""
    from eigenhelm.metrics.cyclomatic import compute

    m = compute(python_quicksort_source, "python")
    expected = m.complexity / m.nloc if m.nloc > 0 else 0.0
    assert m.density == pytest.approx(expected)


def test_cyclomatic_javascript(js_quicksort_source):
    """Language-agnostic: works for JavaScript."""
    from eigenhelm.metrics.cyclomatic import compute

    m = compute(js_quicksort_source, "javascript")
    assert m.complexity >= 1
    assert m.nloc > 0


def test_cyclomatic_go(go_quicksort_source):
    """Language-agnostic: works for Go."""
    from eigenhelm.metrics.cyclomatic import compute

    m = compute(go_quicksort_source, "go")
    assert m.complexity >= 1


def test_cyclomatic_rust(rust_quicksort_source):
    """Language-agnostic: works for Rust."""
    from eigenhelm.metrics.cyclomatic import compute

    m = compute(rust_quicksort_source, "rust")
    assert m.complexity >= 1


def test_cyclomatic_java(java_quicksort_source):
    """Language-agnostic: works for Java."""
    from eigenhelm.metrics.cyclomatic import compute

    m = compute(java_quicksort_source, "java")
    assert m.complexity >= 1

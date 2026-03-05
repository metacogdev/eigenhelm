"""Integration tests: end-to-end extraction and projection pipeline.

Covers US1 (single extract), US2 (batch), US3 (projection), and
performance budget (SC-003: <50ms p95).
"""

from __future__ import annotations

import pathlib
import time

import numpy as np
import pytest

FIXTURES_DIR = pathlib.Path(__file__).parent.parent / "fixtures"

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# US1: single code block extraction
# ---------------------------------------------------------------------------


def test_extract_python_returns_feature_vectors(python_quicksort_source):
    """extract() returns at least one FeatureVector for valid Python."""
    from eigenhelm.virtue_extractor import VirtueExtractor

    extractor = VirtueExtractor()
    vectors = extractor.extract(python_quicksort_source, "python")

    assert len(vectors) >= 1
    for v in vectors:
        assert v.values.shape == (69,)
        assert v.values.dtype == np.float64


def test_extract_preserves_language(python_quicksort_source):
    """Extracted CodeUnit carries the correct language annotation."""
    from eigenhelm.virtue_extractor import VirtueExtractor

    vecs = VirtueExtractor().extract(python_quicksort_source, "python")
    for v in vecs:
        assert v.code_unit.language == "python"


def test_extract_deterministic(python_quicksort_source):
    """SC-001: identical source → identical feature vectors."""
    from eigenhelm.virtue_extractor import VirtueExtractor

    ext = VirtueExtractor()
    v1 = ext.extract(python_quicksort_source, "python")
    v2 = ext.extract(python_quicksort_source, "python")

    assert len(v1) == len(v2)
    for a, b in zip(v1, v2, strict=True):
        np.testing.assert_array_equal(a.values, b.values)


def test_extract_language_agnostic(
    python_quicksort_source,
    js_quicksort_source,
    go_quicksort_source,
    rust_quicksort_source,
    java_quicksort_source,
):
    """SC-004: extraction works for all 5 alpha languages."""
    from eigenhelm.virtue_extractor import VirtueExtractor

    ext = VirtueExtractor()
    for source, lang in [
        (python_quicksort_source, "python"),
        (js_quicksort_source, "javascript"),
        (go_quicksort_source, "go"),
        (rust_quicksort_source, "rust"),
        (java_quicksort_source, "java"),
    ]:
        vectors = ext.extract(source, lang)
        assert len(vectors) >= 1, f"No vectors for {lang}"
        assert vectors[0].values.shape == (69,)


def test_wl_histogram_sums_to_one(python_quicksort_source):
    """WL histogram portion (indices 5-68) sums to ~1.0."""
    from eigenhelm.virtue_extractor import VirtueExtractor

    vecs = VirtueExtractor().extract(python_quicksort_source, "python")
    for v in vecs:
        wl_sum = v.values[5:].sum()
        assert pytest.approx(wl_sum, abs=1e-6) == 1.0 or wl_sum == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# US2: batch extraction
# ---------------------------------------------------------------------------


def test_batch_extraction_multi_language(
    python_quicksort_source,
    js_quicksort_source,
    go_quicksort_source,
):
    """extract_batch() returns vectors for all submitted files."""
    from eigenhelm.virtue_extractor import VirtueExtractor

    ext = VirtueExtractor()
    files = [
        (python_quicksort_source, "python", "python_qs.py"),
        (js_quicksort_source, "javascript", "js_qs.js"),
        (go_quicksort_source, "go", "go_qs.go"),
    ]
    results = ext.extract_batch(files)
    assert len(results) >= 3
    for v in results:
        assert v.values.shape == (69,)


def test_batch_unsupported_language_does_not_crash(python_quicksort_source):
    """US2/AC3: unsupported language returns warning, doesn't halt batch."""
    from eigenhelm.virtue_extractor import VirtueExtractor

    ext = VirtueExtractor()
    files = [
        (python_quicksort_source, "python", "ok.py"),
        ("print('hi')", "brainfuck", "bad.bf"),  # unsupported
        (python_quicksort_source, "python", "also_ok.py"),
    ]
    results = ext.extract_batch(files)
    # At least the two Python files should succeed
    ok_vectors = [v for v in results if not v.partial_parse]
    assert len(ok_vectors) >= 2

    bad_vectors = [v for v in results if v.partial_parse and v.warning]
    assert len(bad_vectors) >= 1
    warn = bad_vectors[0].warning.lower()
    assert "brainfuck" in warn or "unsupported" in warn


def test_batch_multi_function_file():
    """US2/AC2: multi-function file yields one vector per function."""
    from eigenhelm.virtue_extractor import VirtueExtractor

    source = (
        "def foo(x):\n    return x + 1\n\n"
        "def bar(x):\n    return x * 2\n\n"
        "def baz(x):\n    return x - 1\n"
    )
    vectors = VirtueExtractor().extract(source, "python")
    # Should have 3 functions
    assert len(vectors) == 3
    names = {v.code_unit.name for v in vectors}
    assert names == {"foo", "bar", "baz"}


# ---------------------------------------------------------------------------
# US3: eigenspace projection
# ---------------------------------------------------------------------------


def test_project_python_quicksort(python_quicksort_source, synthetic_model):
    """Project a real feature vector with synthetic model."""
    from eigenhelm.virtue_extractor import VirtueExtractor

    ext = VirtueExtractor()
    vectors = ext.extract(python_quicksort_source, "python")
    assert vectors

    result = ext.project(vectors[0], synthetic_model)
    assert result.coordinates.shape == (3,)
    assert result.l_drift >= 0.0
    assert result.l_virtue >= 0.0
    assert result.quality_flag in ("nominal", "high_drift", "partial_input")


# ---------------------------------------------------------------------------
# Performance: SC-003 (<50ms p95 per function)
# ---------------------------------------------------------------------------


def test_performance_single_extract_under_50ms(python_quicksort_source):
    """SC-003: single extraction must complete in <50ms (p95 approx via median)."""
    from eigenhelm.virtue_extractor import VirtueExtractor

    ext = VirtueExtractor()
    N = 20
    times = []
    for _ in range(N):
        t0 = time.perf_counter()
        ext.extract(python_quicksort_source, "python")
        times.append(time.perf_counter() - t0)

    p95_ms = np.quantile(times, 0.95) * 1000
    assert p95_ms < 50.0, f"p95 extraction time {p95_ms:.1f}ms exceeds 50ms budget"


def test_performance_javascript_under_50ms(js_quicksort_source):
    """SC-003: JavaScript extraction under 50ms."""
    from eigenhelm.virtue_extractor import VirtueExtractor

    ext = VirtueExtractor()
    N = 20
    times = []
    for _ in range(N):
        t0 = time.perf_counter()
        ext.extract(js_quicksort_source, "javascript")
        times.append(time.perf_counter() - t0)

    p95_ms = np.quantile(times, 0.95) * 1000
    assert p95_ms < 50.0, f"JS p95 {p95_ms:.1f}ms exceeds 50ms budget"


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_extract_empty_string():
    """Empty string returns empty list, no exception."""
    from eigenhelm.virtue_extractor import VirtueExtractor

    vecs = VirtueExtractor().extract("", "python")
    assert vecs == []


def test_extract_syntax_error():
    """Partial AST: sets partial_parse=True, returns usable vector."""
    from eigenhelm.virtue_extractor import VirtueExtractor

    source = "def foo(:\n    pass\n"  # syntax error
    vecs = VirtueExtractor().extract(source, "python")
    # Tree-sitter handles partial ASTs; we should get a result and it
    # must be flagged as partial.
    assert isinstance(vecs, list)
    if vecs:
        assert any(v.partial_parse for v in vecs)


def test_extract_unsupported_language_raises():
    """UnsupportedLanguageError raised for unknown language."""
    from eigenhelm.virtue_extractor import VirtueExtractor

    from eigenhelm.models import UnsupportedLanguageError

    with pytest.raises(UnsupportedLanguageError):
        VirtueExtractor().extract("print('hi')", "cobol")

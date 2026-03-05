"""Interface contract tests for IVirtueExtractor.

These tests verify that VirtueExtractor satisfies every invariant
declared in the IVirtueExtractor contract (contracts/ivirtue_extractor.md).
"""

from __future__ import annotations

import numpy as np
import pytest

from eigenhelm.models import FEATURE_DIM, WL_BINS

pytestmark = pytest.mark.contract


# ---------------------------------------------------------------------------
# Contract: extract() invariants
# ---------------------------------------------------------------------------


class TestExtractContract:
    def test_returns_list(self, python_quicksort_source):
        """extract() always returns a list."""
        from eigenhelm.virtue_extractor import VirtueExtractor

        result = VirtueExtractor().extract(python_quicksort_source, "python")
        assert isinstance(result, list)

    def test_feature_vector_shape(self, python_quicksort_source):
        """Invariant 3: values.shape == (69,)."""
        from eigenhelm.virtue_extractor import VirtueExtractor

        vectors = VirtueExtractor().extract(python_quicksort_source, "python")
        for v in vectors:
            assert v.values.shape == (FEATURE_DIM,)

    def test_feature_vector_dtype(self, python_quicksort_source):
        """Invariant 3: values.dtype == float64."""
        from eigenhelm.virtue_extractor import VirtueExtractor

        vectors = VirtueExtractor().extract(python_quicksort_source, "python")
        for v in vectors:
            assert v.values.dtype == np.float64

    def test_deterministic(self, python_quicksort_source):
        """Invariant 1: identical input → identical output."""
        from eigenhelm.virtue_extractor import VirtueExtractor

        ext = VirtueExtractor()
        v1 = ext.extract(python_quicksort_source, "python")
        v2 = ext.extract(python_quicksort_source, "python")
        assert len(v1) == len(v2)
        for a, b in zip(v1, v2, strict=True):
            np.testing.assert_array_equal(a.values, b.values)

    def test_wl_histogram_normalized(self, python_quicksort_source):
        """Invariant 4: WL histogram bins (indices 5-68) sum to ~1.0."""
        from eigenhelm.virtue_extractor import VirtueExtractor

        vectors = VirtueExtractor().extract(python_quicksort_source, "python")
        for v in vectors:
            wl = v.values[5:]
            assert wl.shape == (WL_BINS,)
            total = wl.sum()
            assert total == pytest.approx(1.0, abs=1e-6) or total == 0.0

    def test_unsupported_language_raises(self):
        """Invariant 7: UnsupportedLanguageError for unknown language."""
        from eigenhelm.virtue_extractor import VirtueExtractor

        from eigenhelm.models import UnsupportedLanguageError

        with pytest.raises(UnsupportedLanguageError) as exc_info:
            VirtueExtractor().extract("code", "cobol")
        assert "cobol" in str(exc_info.value)

    def test_empty_source_returns_empty(self):
        """Empty string → empty list, no exception."""
        from eigenhelm.virtue_extractor import VirtueExtractor

        result = VirtueExtractor().extract("", "python")
        assert result == []

    def test_empty_source_whitespace_returns_empty(self):
        """Whitespace-only string → empty list."""
        from eigenhelm.virtue_extractor import VirtueExtractor

        result = VirtueExtractor().extract("   \n\t  ", "python")
        assert result == []


# ---------------------------------------------------------------------------
# Contract: extract_batch() invariants
# ---------------------------------------------------------------------------


class TestExtractBatchContract:
    def test_returns_list(self, python_quicksort_source):
        """extract_batch() returns a list."""
        from eigenhelm.virtue_extractor import VirtueExtractor

        result = VirtueExtractor().extract_batch([(python_quicksort_source, "python", "f.py")])
        assert isinstance(result, list)

    def test_batch_no_raise_on_unsupported(self, python_quicksort_source):
        """Invariant 5: unsupported language produces warning, not exception."""
        from eigenhelm.virtue_extractor import VirtueExtractor

        files = [
            (python_quicksort_source, "python", "ok.py"),
            ("code", "cobol", "bad.cob"),
        ]
        # Must not raise
        results = VirtueExtractor().extract_batch(files)
        assert isinstance(results, list)
        assert len(results) >= 1

    def test_batch_unsupported_has_warning(self):
        """Unsupported language entries have a non-empty warning."""
        from eigenhelm.virtue_extractor import VirtueExtractor

        files = [("code", "cobol", "bad.cob")]
        results = VirtueExtractor().extract_batch(files)
        assert len(results) == 1
        assert results[0].partial_parse is True
        assert results[0].warning is not None
        assert len(results[0].warning) > 0

    def test_batch_all_vectors_correct_shape(self, python_quicksort_source):
        """All returned vectors have correct shape."""
        from eigenhelm.virtue_extractor import VirtueExtractor

        files = [(python_quicksort_source, "python", f"f{i}.py") for i in range(3)]
        results = VirtueExtractor().extract_batch(files)
        for v in results:
            assert v.values.shape == (FEATURE_DIM,)


# ---------------------------------------------------------------------------
# Contract: project() invariants
# ---------------------------------------------------------------------------


class TestProjectContract:
    def test_project_requires_model(self, python_quicksort_source, synthetic_model):
        """project() works with a valid model."""
        from eigenhelm.virtue_extractor import VirtueExtractor

        ext = VirtueExtractor()
        vectors = ext.extract(python_quicksort_source, "python")
        assert vectors
        result = ext.project(vectors[0], synthetic_model)
        assert result.coordinates.shape == (synthetic_model.n_components,)

    def test_project_quality_flag_values(self, python_quicksort_source, synthetic_model):
        """quality_flag is one of the three allowed values."""
        from eigenhelm.virtue_extractor import VirtueExtractor

        ext = VirtueExtractor()
        vectors = ext.extract(python_quicksort_source, "python")
        result = ext.project(vectors[0], synthetic_model)
        assert result.quality_flag in ("nominal", "partial_input", "high_drift")

    def test_project_l_drift_non_negative(self, python_quicksort_source, synthetic_model):
        """L_drift >= 0."""
        from eigenhelm.virtue_extractor import VirtueExtractor

        ext = VirtueExtractor()
        vectors = ext.extract(python_quicksort_source, "python")
        result = ext.project(vectors[0], synthetic_model)
        assert result.l_drift >= 0.0

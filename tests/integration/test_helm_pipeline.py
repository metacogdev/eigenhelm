"""Integration tests for Stage 1→2→3 pipeline: DynamicHelm end-to-end.

Tests the full pipeline: VirtueExtractor → AestheticCritic → DynamicHelm.
"""

from __future__ import annotations

import pytest
from eigenhelm.helm import DynamicHelm, EvaluationRequest

CLEAN_CODE = (
    """\
def add(a, b):
    return a + b
"""
    * 10
)

REPETITIVE_CODE = "x = 1\ny = 1\nz = 1\n" * 50

QUICKSORT = """\
def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left  = [x for x in arr if x < pivot]
    mid   = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + mid + quicksort(right)
"""


@pytest.mark.integration
class TestHelmPipelineNoEigenspace:
    """Tests without eigenspace (low-confidence mode)."""

    def test_quicksort_returns_valid_response(self):
        helm = DynamicHelm()
        r = helm.evaluate(EvaluationRequest(source=QUICKSORT, language="python"))
        assert r.decision in {"accept", "warn", "reject"}
        assert 0.0 <= r.score <= 1.0
        assert r.structural_confidence == "low"
        assert r.warning is not None

    def test_empty_source_accept(self):
        helm = DynamicHelm()
        r = helm.evaluate(EvaluationRequest(source="", language="python"))
        assert r.decision == "accept"
        assert r.score == 0.0

    def test_decision_consistent_with_score(self):
        helm = DynamicHelm()
        r = helm.evaluate(EvaluationRequest(source=QUICKSORT, language="python"))
        if r.score < helm._accept_threshold:
            assert r.decision == "accept"
        elif r.score > helm._reject_threshold:
            assert r.decision == "reject"
        else:
            assert r.decision == "warn"

    def test_score_equals_critique_score_value(self):
        helm = DynamicHelm()
        r = helm.evaluate(EvaluationRequest(source=QUICKSORT, language="python"))
        assert r.score == r.critique.score.value

    def test_structural_confidence_mirrors_critique(self):
        helm = DynamicHelm()
        r = helm.evaluate(EvaluationRequest(source=QUICKSORT, language="python"))
        assert r.structural_confidence == r.critique.score.structural_confidence


@pytest.mark.integration
class TestHelmPipelineWithEigenspace:
    """Tests with synthetic eigenspace (high-confidence mode)."""

    def test_with_eigenspace_high_confidence(self, synthetic_model):
        helm = DynamicHelm(eigenspace=synthetic_model)
        r = helm.evaluate(EvaluationRequest(source=QUICKSORT, language="python"))
        assert r.structural_confidence == "high"
        assert r.critique.score.structural_confidence == "high"

    def test_with_eigenspace_all_four_dimensions(self, synthetic_model):
        helm = DynamicHelm(eigenspace=synthetic_model)
        r = helm.evaluate(EvaluationRequest(source=QUICKSORT, language="python"))
        expected_dims = {
            "manifold_drift",
            "manifold_alignment",
            "token_entropy",
            "compression_structure",
        }
        assert set(r.critique.score.weights.keys()) == expected_dims

    def test_with_eigenspace_no_warning(self, synthetic_model):
        """With eigenspace and supported language, warning should be None."""
        helm = DynamicHelm(eigenspace=synthetic_model)
        r = helm.evaluate(EvaluationRequest(source=QUICKSORT, language="python"))
        assert r.warning is None

    def test_with_eigenspace_score_bounded(self, synthetic_model):
        helm = DynamicHelm(eigenspace=synthetic_model)
        r = helm.evaluate(EvaluationRequest(source=QUICKSORT, language="python"))
        assert 0.0 <= r.score <= 1.0

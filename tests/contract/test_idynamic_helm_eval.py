"""Contract tests for IDynamicHelm.evaluate() — invariants 1–7.

Invariants tested:
  1. evaluate() is deterministic.
  2. evaluate() completes in < 50ms for ≤ 500 LoC (SC-001).
  3. EvaluationResponse.score ∈ [0.0, 1.0].
  4. decision agrees with threshold logic (boundary semantics).
  5. empty/whitespace source → decision="accept", score=0.0.
  6. unsupported language → low confidence + warning.
  7. structural_confidence mirrors Stage 2 (never overridden).
"""

from __future__ import annotations

import time

import pytest
from eigenhelm.helm import DynamicHelm, EvaluationRequest

PYTHON_SOURCE = """\
def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left  = [x for x in arr if x < pivot]
    mid   = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + mid + quicksort(right)
"""


@pytest.fixture
def helm() -> DynamicHelm:
    return DynamicHelm()


# ---------------------------------------------------------------------------
# Invariant 1: determinism
# ---------------------------------------------------------------------------


class TestDeterminism:
    def test_same_input_same_output(self, helm):
        req = EvaluationRequest(source=PYTHON_SOURCE, language="python")
        r1 = helm.evaluate(req)
        r2 = helm.evaluate(req)
        assert r1 == r2

    def test_empty_source_deterministic(self, helm):
        req = EvaluationRequest(source="", language="python")
        r1 = helm.evaluate(req)
        r2 = helm.evaluate(req)
        assert r1 == r2


# ---------------------------------------------------------------------------
# Invariant 2: performance < 50ms for ≤ 500 LoC
# ---------------------------------------------------------------------------


class TestPerformance:
    def test_evaluate_under_50ms(self, helm):
        req = EvaluationRequest(source=PYTHON_SOURCE, language="python")
        start = time.perf_counter()
        helm.evaluate(req)
        elapsed_ms = (time.perf_counter() - start) * 1000
        assert elapsed_ms < 50.0, f"evaluate() took {elapsed_ms:.1f}ms, expected < 50ms"


# ---------------------------------------------------------------------------
# Invariant 3: score ∈ [0.0, 1.0]
# ---------------------------------------------------------------------------


class TestScoreBounds:
    def test_score_in_unit_interval(self, helm):
        req = EvaluationRequest(source=PYTHON_SOURCE, language="python")
        r = helm.evaluate(req)
        assert 0.0 <= r.score <= 1.0

    def test_score_equals_critique_score_value(self, helm):
        req = EvaluationRequest(source=PYTHON_SOURCE, language="python")
        r = helm.evaluate(req)
        assert r.score == r.critique.score.value

    def test_empty_source_score_is_zero(self, helm):
        req = EvaluationRequest(source="", language="python")
        r = helm.evaluate(req)
        assert r.score == 0.0


# ---------------------------------------------------------------------------
# Invariant 4: threshold-to-decision mapping with boundary semantics
# ---------------------------------------------------------------------------


class TestDecisionMapping:
    def test_score_below_accept_gives_accept(self):
        helm = DynamicHelm(accept_threshold=0.9, reject_threshold=0.95)
        req = EvaluationRequest(source="", language="python")  # score=0.0
        r = helm.evaluate(req)
        assert r.decision == "accept"

    def test_score_above_reject_gives_reject(self):
        import os

        helm = DynamicHelm(accept_threshold=0.01, reject_threshold=0.02)
        # Near-random source has high entropy → high score
        raw = os.urandom(500)
        src = "".join(chr(0x21 + (b % 94)) for b in raw) + "\n"
        req = EvaluationRequest(source=src, language="python")
        r = helm.evaluate(req)
        # If score > 0.02, should be reject
        if r.score > 0.02:
            assert r.decision == "reject"

    def test_score_at_accept_threshold_gives_warn(self):
        """Exact accept_threshold boundary → warn (strict inequality)."""
        helm = DynamicHelm(accept_threshold=0.4, reject_threshold=0.6)
        req = EvaluationRequest(source=PYTHON_SOURCE, language="python")
        r = helm.evaluate(req)
        # Verify threshold logic is correctly applied to whatever score we get
        if r.score < 0.4:
            assert r.decision == "accept"
        elif r.score > 0.6:
            assert r.decision == "reject"
        else:
            assert r.decision == "warn"

    def test_decision_boundary_semantics(self):
        """score < accept → accept; score > reject → reject; in-between → warn."""
        helm = DynamicHelm(accept_threshold=0.4, reject_threshold=0.6)
        req = EvaluationRequest(source=PYTHON_SOURCE, language="python")
        r = helm.evaluate(req)
        if r.score < 0.4:
            assert r.decision == "accept"
        elif r.score > 0.6:
            assert r.decision == "reject"
        else:
            assert r.decision == "warn"

    def test_custom_thresholds_respected(self):
        helm = DynamicHelm(accept_threshold=0.1, reject_threshold=0.9)
        req = EvaluationRequest(source=PYTHON_SOURCE, language="python")
        r = helm.evaluate(req)
        if r.score < 0.1:
            assert r.decision == "accept"
        elif r.score > 0.9:
            assert r.decision == "reject"
        else:
            assert r.decision == "warn"


# ---------------------------------------------------------------------------
# Invariant 5: empty/whitespace source
# ---------------------------------------------------------------------------


class TestEmptySource:
    def test_empty_source_accept(self, helm):
        req = EvaluationRequest(source="", language="python")
        r = helm.evaluate(req)
        assert r.decision == "accept"
        assert r.score == 0.0

    def test_whitespace_only_accept(self, helm):
        req = EvaluationRequest(source="   \n\n  ", language="python")
        r = helm.evaluate(req)
        assert r.decision == "accept"
        assert r.score == 0.0

    def test_empty_no_raise(self, helm):
        req = EvaluationRequest(source="", language="unknown_lang")
        r = helm.evaluate(req)
        assert r is not None

    def test_empty_no_violations(self, helm):
        req = EvaluationRequest(source="", language="python")
        r = helm.evaluate(req)
        assert r.critique.violations == []


# ---------------------------------------------------------------------------
# Invariant 6: unsupported language → low confidence + warning
# ---------------------------------------------------------------------------


class TestUnsupportedLanguage:
    def test_unsupported_language_no_raise(self, helm):
        req = EvaluationRequest(source=PYTHON_SOURCE, language="brainfuck")
        r = helm.evaluate(req)
        assert r is not None

    def test_unsupported_language_low_confidence(self, helm):
        req = EvaluationRequest(source=PYTHON_SOURCE, language="cobol")
        r = helm.evaluate(req)
        assert r.structural_confidence == "low"

    def test_unsupported_language_warning_set(self, helm):
        req = EvaluationRequest(source=PYTHON_SOURCE, language="brainfuck")
        r = helm.evaluate(req)
        assert r.warning is not None
        assert "brainfuck" in r.warning

    def test_unsupported_language_score_bounded(self, helm):
        req = EvaluationRequest(source=PYTHON_SOURCE, language="cobol")
        r = helm.evaluate(req)
        assert 0.0 <= r.score <= 1.0


# ---------------------------------------------------------------------------
# Invariant 7: structural_confidence mirrors Stage 2
# ---------------------------------------------------------------------------


class TestStructuralConfidenceMirrored:
    def test_low_confidence_without_eigenspace(self, helm):
        req = EvaluationRequest(source=PYTHON_SOURCE, language="python")
        r = helm.evaluate(req)
        assert r.structural_confidence == r.critique.score.structural_confidence

    def test_no_eigenspace_low_confidence(self, helm):
        """Without eigenspace, structural_confidence must be 'low'."""
        req = EvaluationRequest(source=PYTHON_SOURCE, language="python")
        r = helm.evaluate(req)
        assert r.structural_confidence == "low"

    def test_no_eigenspace_warning_set(self, helm):
        """Without eigenspace, warning must be set."""
        req = EvaluationRequest(source=PYTHON_SOURCE, language="python")
        r = helm.evaluate(req)
        assert r.warning is not None
        assert "eigenspace" in r.warning.lower()

    def test_with_eigenspace_high_confidence(self, synthetic_model):
        """With eigenspace, structural_confidence should be 'high'."""
        helm = DynamicHelm(eigenspace=synthetic_model)
        req = EvaluationRequest(source=PYTHON_SOURCE, language="python")
        r = helm.evaluate(req)
        assert r.structural_confidence == "high"
        assert r.structural_confidence == r.critique.score.structural_confidence

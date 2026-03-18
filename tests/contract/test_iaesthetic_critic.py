"""Contract tests for IAestheticCritic — verifies all contract invariants.

Invariants tested:
  1. evaluate() is deterministic.
  2. score() == evaluate().score.value.
  4. AestheticScore.value ∈ [0.0, 1.0].
  5. sum(AestheticScore.weights.values()) == 1.0.
  6. violations sorted descending by contribution, ≤ top_n entries.
  7. evaluate() never raises on unsupported language.
  8. evaluate() never raises on empty source → loss=0.0, quality="accept", violations=[].
  9. AestheticMetrics.birkhoff_measure ∈ [0.0, 1.0].
"""

from __future__ import annotations

import pytest
from eigenhelm.critic import AestheticCritic, Critique

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

REPETITIVE_SOURCE = "x = 1\n" * 100


@pytest.fixture
def critic() -> AestheticCritic:
    return AestheticCritic()


# ---------------------------------------------------------------------------
# Invariant 1: determinism
# ---------------------------------------------------------------------------


class TestDeterminism:
    def test_evaluate_same_input_same_output(self, critic):
        c1 = critic.evaluate(PYTHON_SOURCE, "python")
        c2 = critic.evaluate(PYTHON_SOURCE, "python")
        assert c1 == c2

    def test_score_same_input_same_output(self, critic):
        assert critic.score(PYTHON_SOURCE, "python") == critic.score(PYTHON_SOURCE, "python")

    def test_repetitive_source_deterministic(self, critic):
        c1 = critic.evaluate(REPETITIVE_SOURCE, "python")
        c2 = critic.evaluate(REPETITIVE_SOURCE, "python")
        assert c1 == c2


# ---------------------------------------------------------------------------
# Invariant 2: score() == evaluate().score.value
# ---------------------------------------------------------------------------


class TestScoreEquivalence:
    def test_score_equals_evaluate_score_value(self, critic):
        s = critic.score(PYTHON_SOURCE, "python")
        c = critic.evaluate(PYTHON_SOURCE, "python")
        assert s == c.score.value

    def test_score_equals_evaluate_for_empty(self, critic):
        assert critic.score("", "python") == critic.evaluate("", "python").score.value

    def test_score_equals_evaluate_for_repetitive(self, critic):
        s = critic.score(REPETITIVE_SOURCE, "python")
        c = critic.evaluate(REPETITIVE_SOURCE, "python")
        assert s == c.score.value


# ---------------------------------------------------------------------------
# Invariant 4: AestheticScore.value ∈ [0.0, 1.0]
# ---------------------------------------------------------------------------


class TestScoreBounds:
    def test_score_in_unit_interval(self, critic):
        c = critic.evaluate(PYTHON_SOURCE, "python")
        assert 0.0 <= c.score.value <= 1.0

    def test_score_in_unit_interval_repetitive(self, critic):
        c = critic.evaluate(REPETITIVE_SOURCE, "python")
        assert 0.0 <= c.score.value <= 1.0

    def test_scalar_score_in_unit_interval(self, critic):
        s = critic.score(PYTHON_SOURCE, "python")
        assert 0.0 <= s <= 1.0

    def test_empty_source_loss_is_zero(self, critic):
        c = critic.evaluate("", "python")
        assert c.score.value == 0.0


# ---------------------------------------------------------------------------
# Invariant 5: sum(weights) == 1.0
# ---------------------------------------------------------------------------


class TestWeightsSumToOne:
    def test_weights_sum_low_confidence(self, critic):
        c = critic.evaluate(PYTHON_SOURCE, "python")
        assert abs(sum(c.score.weights.values()) - 1.0) < 1e-9

    def test_weights_sum_empty_source(self, critic):
        c = critic.evaluate("", "python")
        assert abs(sum(c.score.weights.values()) - 1.0) < 1e-9

    def test_weights_contain_all_four_dimensions(self, critic):
        c = critic.evaluate(PYTHON_SOURCE, "python")
        expected_dims = {
            "manifold_drift",
            "manifold_alignment",
            "token_entropy",
            "compression_structure",
            "ncd_exemplar_distance",
        }
        assert set(c.score.weights.keys()) == expected_dims


# ---------------------------------------------------------------------------
# Invariant 6: violations sorted descending, ≤ top_n
# ---------------------------------------------------------------------------


class TestViolationOrdering:
    def test_violations_sorted_descending(self, critic):
        c = critic.evaluate(REPETITIVE_SOURCE, "python")
        contribs = [v.contribution for v in c.violations]
        assert contribs == sorted(contribs, reverse=True)

    def test_violations_at_most_top_n(self, critic):
        c = critic.evaluate(REPETITIVE_SOURCE, "python", top_n=2)
        assert len(c.violations) <= 2

    def test_violations_at_most_three_by_default(self, critic):
        c = critic.evaluate(PYTHON_SOURCE, "python")
        assert len(c.violations) <= 3

    def test_violations_top_n_stored(self, critic):
        c = critic.evaluate(PYTHON_SOURCE, "python", top_n=2)
        assert c.top_n == 2


# ---------------------------------------------------------------------------
# Violation raw_value vs normalized_value (H-1 regression guard)
# ---------------------------------------------------------------------------


class TestViolationRawValues:
    def test_token_entropy_raw_value_is_bits_not_normalized(self, critic):
        # raw_value for token_entropy must be the entropy in bits/byte (0–8 range),
        # not the normalized 1.0 - entropy/8.0 value (0–1 range).
        c = critic.evaluate(PYTHON_SOURCE, "python")
        entropy_violations = [v for v in c.violations if v.dimension == "token_entropy"]
        if entropy_violations:
            v = entropy_violations[0]
            # raw bits/byte ∈ [0, 8], normalized ∈ [0, 1]
            assert v.raw_value > 1.0 or (
                v.raw_value < 1.0 and abs(v.normalized_value - (1.0 - v.raw_value / 8.0)) < 1e-9
            ), "raw_value should be entropy in bits/byte"
            # The critical check: raw != normalized when entropy > 1 bit/byte
            if v.raw_value > 1.0:
                assert v.raw_value != v.normalized_value

    def test_token_entropy_raw_normalized_relationship(self, critic):
        # normalized_value must equal 1.0 - raw_value / 8.0 for token_entropy (013 polarity fix).
        c = critic.evaluate(REPETITIVE_SOURCE, "python")
        for v in c.violations:
            if v.dimension == "token_entropy":
                assert abs(v.normalized_value - (1.0 - v.raw_value / 8.0)) < 1e-9

    def test_compression_structure_raw_value_is_birkhoff(self, critic):
        # raw_value for compression_structure is birkhoff_measure directly (013 polarity fix),
        # same as normalized_value since it's already in [0, 1].
        c = critic.evaluate(PYTHON_SOURCE, "python")
        for v in c.violations:
            if v.dimension == "compression_structure":
                assert 0.0 <= v.raw_value <= 1.0
                assert abs(v.raw_value - v.normalized_value) < 1e-9


# ---------------------------------------------------------------------------
# Invariant 7: never raises on unsupported language
# ---------------------------------------------------------------------------


class TestGracefulDegradation:
    def test_unsupported_language_no_raise(self, critic):
        c = critic.evaluate(PYTHON_SOURCE, "brainfuck")
        assert isinstance(c, Critique)

    def test_unsupported_language_low_confidence(self, critic):
        c = critic.evaluate(PYTHON_SOURCE, "cobol")
        assert c.score.structural_confidence == "low"


# ---------------------------------------------------------------------------
# Invariant 8: empty source → loss=0.0, quality="accept", violations=[]
# ---------------------------------------------------------------------------


class TestEmptySource:
    def test_empty_returns_zero_loss(self, critic):
        c = critic.evaluate("", "python")
        assert c.score.value == 0.0

    def test_empty_returns_accept(self, critic):
        c = critic.evaluate("", "python")
        assert c.quality_assessment == "accept"

    def test_empty_returns_no_violations(self, critic):
        c = critic.evaluate("", "python")
        assert c.violations == []

    def test_empty_does_not_raise(self, critic):
        c = critic.evaluate("", "unknown_lang")
        assert isinstance(c, Critique)


# ---------------------------------------------------------------------------
# Invariant 9: birkhoff_measure ∈ [0.0, 1.0]
# ---------------------------------------------------------------------------


class TestBirkhoffBounds:
    def test_birkhoff_in_unit_interval(self, critic):
        c = critic.evaluate(PYTHON_SOURCE, "python")
        assert 0.0 <= c.metrics.birkhoff_measure <= 1.0

    def test_birkhoff_in_unit_interval_repetitive(self, critic):
        c = critic.evaluate(REPETITIVE_SOURCE, "python")
        assert 0.0 <= c.metrics.birkhoff_measure <= 1.0

    def test_birkhoff_none_for_short_source(self, critic):
        c = critic.evaluate("x = 1\n", "python")
        # Short source → compression_ratio is None → birkhoff = 0.0
        assert c.metrics.birkhoff_measure == 0.0
        assert c.metrics.compression_ratio is None


# ---------------------------------------------------------------------------
# Quality thresholds
# ---------------------------------------------------------------------------


class TestQualityThresholds:
    def test_accept_below_0_4(self):
        # Force a known low-loss source (highly repetitive → low entropy + low compression penalty)
        critic = AestheticCritic()
        c = critic.evaluate(REPETITIVE_SOURCE, "python")
        # Verify threshold logic: accept if < 0.4, marginal if [0.4, 0.6), reject if ≥ 0.6
        if c.score.value < 0.4:
            assert c.quality_assessment == "accept"
        elif c.score.value < 0.6:
            assert c.quality_assessment == "marginal"
        else:
            assert c.quality_assessment == "reject"

    def test_custom_thresholds(self):
        critic = AestheticCritic(reject_threshold=0.5, marginal_threshold=0.3)
        c = critic.evaluate(PYTHON_SOURCE, "python")
        if c.score.value >= 0.5:
            assert c.quality_assessment == "reject"
        elif c.score.value >= 0.3:
            assert c.quality_assessment == "marginal"
        else:
            assert c.quality_assessment == "accept"


# ---------------------------------------------------------------------------
# sigma_virtue parameterization (006-norm-calibration)
# ---------------------------------------------------------------------------


class TestSigmaVirtue:
    """Contract: sigma_virtue normalizes manifold_alignment dimension."""

    def test_stores_sigma_virtue(self):
        critic = AestheticCritic(sigma_virtue=5.0)
        assert critic.sigma_virtue == 5.0

    def test_default_sigma_virtue_is_one(self):
        critic = AestheticCritic()
        assert critic.sigma_virtue == 1.0

    def test_sigma_virtue_zero_raises(self):
        with pytest.raises(ValueError, match="sigma_virtue"):
            AestheticCritic(sigma_virtue=0.0)

    def test_sigma_virtue_negative_raises(self):
        with pytest.raises(ValueError, match="sigma_virtue"):
            AestheticCritic(sigma_virtue=-1.0)

    def test_normalize_dimensions_uses_sigma_virtue(self):
        """manifold_alignment = min(l_virtue / sigma_virtue, 1.0)."""
        import numpy as np

        from eigenhelm.models import ProjectionResult

        proj = ProjectionResult(
            coordinates=np.zeros(3),
            l_drift=0.5,
            l_virtue=5.0,
            quality_flag="nominal",
        )
        # With sigma_virtue=10.0: min(5.0/10.0, 1.0) = 0.5
        critic_calibrated = AestheticCritic(sigma_virtue=10.0)
        norm_calibrated = critic_calibrated._normalize_dimensions(
            critic_calibrated._compute_metrics(PYTHON_SOURCE, "python"), proj
        )
        assert abs(norm_calibrated["manifold_alignment"] - 0.5) < 1e-9

        # With sigma_virtue=1.0: min(5.0/1.0, 1.0) = 1.0
        critic_default = AestheticCritic(sigma_virtue=1.0)
        norm_default = critic_default._normalize_dimensions(
            critic_default._compute_metrics(PYTHON_SOURCE, "python"), proj
        )
        assert abs(norm_default["manifold_alignment"] - 1.0) < 1e-9

    def test_calibrated_sigma_virtue_lowers_score(self):
        """A large sigma_virtue produces a lower score than sigma_virtue=1.0 for the same source."""
        import numpy as np

        from eigenhelm.models import ProjectionResult

        proj = ProjectionResult(
            coordinates=np.zeros(3),
            l_drift=0.1,
            l_virtue=8.0,
            quality_flag="nominal",
        )
        score_default = AestheticCritic(sigma_virtue=1.0).score(PYTHON_SOURCE, "python", proj)
        score_calibrated = AestheticCritic(sigma_virtue=12.0).score(PYTHON_SOURCE, "python", proj)
        assert score_calibrated < score_default

    def test_sigma_virtue_default_backwards_compatible(self):
        """Default sigma_virtue=1.0 reproduces pre-calibration behaviour."""
        import numpy as np

        from eigenhelm.models import ProjectionResult

        proj = ProjectionResult(
            coordinates=np.zeros(3),
            l_drift=0.3,
            l_virtue=0.7,
            quality_flag="nominal",
        )
        critic_explicit = AestheticCritic(sigma_virtue=1.0)
        critic_default = AestheticCritic()
        assert critic_explicit.score(PYTHON_SOURCE, "python", proj) == pytest.approx(
            critic_default.score(PYTHON_SOURCE, "python", proj)
        )


# ---------------------------------------------------------------------------
# 010: Exemplar-based NCD dimension weights (T012)
# ---------------------------------------------------------------------------


class TestExemplarWeights:
    """Contract: weights sum to 1.0 in all exemplar configurations."""

    def _make_exemplar_bytes(self) -> list[bytes]:
        return [
            b"def quicksort(arr):\n    if len(arr) <= 1:\n"
            b"        return arr\n    pivot = arr[0]\n"
            b"    left = [x for x in arr[1:] if x <= pivot]\n"
            b"    right = [x for x in arr[1:] if x > pivot]\n"
            b"    return quicksort(left) + [pivot] + quicksort(right)\n",
        ]

    def test_5_dim_weights_sum_to_1_with_exemplars(self):
        """5-dimension weights sum to 1.0 when projection + exemplars provided."""
        import numpy as np

        from eigenhelm.models import ProjectionResult

        proj = ProjectionResult(
            coordinates=np.zeros(3),
            l_drift=0.3,
            l_virtue=0.5,
            quality_flag="nominal",
        )
        critic = AestheticCritic(exemplars=self._make_exemplar_bytes())
        c = critic.evaluate(PYTHON_SOURCE, "python", projection=proj)
        assert abs(sum(c.score.weights.values()) - 1.0) < 1e-9
        assert "ncd_exemplar_distance" in c.score.weights
        assert c.score.weights["ncd_exemplar_distance"] > 0.0

    def test_4_dim_weights_sum_to_1_without_exemplars(self):
        """4-dimension weights sum to 1.0 when projection only (backward compat)."""
        import numpy as np

        from eigenhelm.models import ProjectionResult

        proj = ProjectionResult(
            coordinates=np.zeros(3),
            l_drift=0.3,
            l_virtue=0.5,
            quality_flag="nominal",
        )
        critic = AestheticCritic()
        c = critic.evaluate(PYTHON_SOURCE, "python", projection=proj)
        assert abs(sum(c.score.weights.values()) - 1.0) < 1e-9

    def test_ncd_zero_weight_when_no_exemplars(self):
        """NCD dimension gets zero weight when no exemplars provided."""
        import numpy as np

        from eigenhelm.models import ProjectionResult

        proj = ProjectionResult(
            coordinates=np.zeros(3),
            l_drift=0.3,
            l_virtue=0.5,
            quality_flag="nominal",
        )
        critic = AestheticCritic()
        c = critic.evaluate(PYTHON_SOURCE, "python", projection=proj)
        assert c.score.weights.get("ncd_exemplar_distance", 0.0) == 0.0

    def test_3_dim_exemplars_only_weights_sum_to_1(self):
        """3-dimension weights sum to 1.0 when exemplars but no projection."""
        critic = AestheticCritic(exemplars=self._make_exemplar_bytes())
        c = critic.evaluate(PYTHON_SOURCE, "python")
        assert abs(sum(c.score.weights.values()) - 1.0) < 1e-9
        assert c.score.weights.get("ncd_exemplar_distance", 0.0) > 0.0

    def test_2_dim_fallback_weights_sum_to_1(self):
        """2-dimension fallback weights sum to 1.0 when neither projection nor exemplars."""
        critic = AestheticCritic()
        c = critic.evaluate(PYTHON_SOURCE, "python")
        assert abs(sum(c.score.weights.values()) - 1.0) < 1e-9

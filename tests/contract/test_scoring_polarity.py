"""Contract tests for scoring polarity (013-signal-polarity).

Verifies:
- Elite code scores lower than terrible code (polarity direction)
- Weight sums equal 1.0 for all 4 configurations
- Pre-013 model loads and scores without error
- Contributions sum to score.value (US2, added after transparency implementation)
"""

from __future__ import annotations

import numpy as np
from eigenhelm.critic import AestheticCritic
from eigenhelm.models import ProjectionResult

ELITE_SOURCE = """\
def quicksort(arr: list[int]) -> list[int]:
    \"\"\"Sort a list using the quicksort algorithm.\"\"\"
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)


def merge_sort(arr: list[int]) -> list[int]:
    \"\"\"Sort a list using merge sort.\"\"\"
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    return _merge(left, right)


def _merge(left: list[int], right: list[int]) -> list[int]:
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result
"""

TERRIBLE_SOURCE = """\
def f(x,y,z,a,b,c,d,e,f,g):
    if x == 1:
        if y == 1:
            if z == 1:
                if a == 1:
                    if b == 1:
                        return 1
                    else:
                        return 0
                else:
                    return 0
            else:
                return 0
        else:
            return 0
    else:
        return 0
def f2(x,y,z,a,b,c,d,e,f,g):
    if x == 1:
        if y == 1:
            if z == 1:
                if a == 1:
                    if b == 1:
                        return 1
                    else:
                        return 0
                else:
                    return 0
            else:
                return 0
        else:
            return 0
    else:
        return 0
def f3(x,y,z,a,b,c,d,e,f,g):
    if x == 1:
        if y == 1:
            if z == 1:
                if a == 1:
                    if b == 1:
                        return 1
                    else:
                        return 0
                else:
                    return 0
            else:
                return 0
        else:
            return 0
    else:
        return 0
"""


class TestPolarityDirection:
    """Elite code MUST score lower (better) than terrible code."""

    def test_elite_lower_than_terrible_2dim(self):
        critic = AestheticCritic()
        elite_score = critic.score(ELITE_SOURCE, "python")
        terrible_score = critic.score(TERRIBLE_SOURCE, "python")
        assert elite_score < terrible_score, (
            f"Polarity inverted: elite={elite_score:.4f} >= terrible={terrible_score:.4f}"
        )

    def test_scores_bounded(self):
        critic = AestheticCritic()
        elite = critic.score(ELITE_SOURCE, "python")
        terrible = critic.score(TERRIBLE_SOURCE, "python")
        assert 0.0 <= elite <= 1.0
        assert 0.0 <= terrible <= 1.0


class TestWeightSumsAllConfigs:
    """Weight sums MUST equal 1.0 for all 4 configurations."""

    def _proj(self) -> ProjectionResult:
        return ProjectionResult(
            coordinates=np.zeros(3),
            l_drift=0.3,
            l_virtue=0.5,
            quality_flag="nominal",
        )

    def _exemplars(self) -> list[bytes]:
        return [b"def quicksort(arr):\n    pass\n" * 5]

    def test_5dim_sum(self):
        critic = AestheticCritic(exemplars=self._exemplars())
        weights = critic._select_weights(self._proj())
        assert abs(sum(weights.values()) - 1.0) < 1e-9

    def test_4dim_sum(self):
        critic = AestheticCritic()
        weights = critic._select_weights(self._proj())
        assert abs(sum(weights.values()) - 1.0) < 1e-9

    def test_3dim_sum(self):
        critic = AestheticCritic(exemplars=self._exemplars())
        weights = critic._select_weights(None)
        assert abs(sum(weights.values()) - 1.0) < 1e-9

    def test_2dim_sum(self):
        critic = AestheticCritic()
        weights = critic._select_weights(None)
        assert abs(sum(weights.values()) - 1.0) < 1e-9


class TestContributionTransparency:
    """Contribution fields MUST be consistent with score and weights."""

    def test_contributions_sum_to_score(self):
        critic = AestheticCritic()
        critique = critic.evaluate(ELITE_SOURCE, "python")
        total = sum(critique.score.contributions.values())
        assert abs(total - critique.score.value) < 0.001, (
            f"Contributions sum {total:.6f} != score {critique.score.value:.6f}"
        )

    def test_contributions_keys_match_weights(self):
        critic = AestheticCritic()
        critique = critic.evaluate(ELITE_SOURCE, "python")
        assert set(critique.score.contributions.keys()) == set(
            critique.score.weights.keys()
        )

    def test_violation_weighted_contribution(self):
        critic = AestheticCritic()
        critique = critic.evaluate(TERRIBLE_SOURCE, "python")
        for v in critique.violations:
            w = critique.score.weights[v.dimension]
            expected = v.normalized_value * w
            assert abs(v.weighted_contribution - expected) < 1e-9, (
                f"{v.dimension}: weighted_contribution={v.weighted_contribution} "
                f"!= normalized({v.normalized_value}) * weight({w}) = {expected}"
            )

    def test_empty_source_contributions_empty(self):
        critic = AestheticCritic()
        critique = critic.evaluate("", "python")
        assert critique.score.contributions == {}


class TestBackwardCompatibility:
    """Pre-013 models load and score without errors."""

    def test_no_projection_no_exemplars_valid_score(self):
        critic = AestheticCritic()
        critique = critic.evaluate(ELITE_SOURCE, "python")
        assert 0.0 <= critique.score.value <= 1.0
        assert critique.score.structural_confidence == "low"

    def test_empty_source_still_zero(self):
        critic = AestheticCritic()
        critique = critic.evaluate("", "python")
        assert critique.score.value == 0.0
        assert critique.quality_assessment == "accept"

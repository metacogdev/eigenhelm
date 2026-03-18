"""Unit tests for normalization polarity direction (013-signal-polarity).

Verifies that _normalize_dimensions() produces correct penalty orientation:
- Low entropy (repetitive) → high penalty
- High entropy (diverse) → low penalty
- High Birkhoff / compressible → high penalty
- Low Birkhoff / unique → low penalty
- Drift/alignment unchanged
"""

from __future__ import annotations

import pytest
from eigenhelm.critic import AestheticCritic, AestheticMetrics


@pytest.fixture
def critic() -> AestheticCritic:
    return AestheticCritic()


class TestTokenEntropyPolarity:
    """Low entropy = repetitive code = high penalty; high entropy = diverse = low penalty."""

    def test_zero_entropy_max_penalty(self, critic):
        metrics = AestheticMetrics(
            entropy=0.0, compression_ratio=0.5, birkhoff_measure=0.5,
            raw_bytes=100, compressed_bytes=50,
        )
        norm = critic._normalize_dimensions(metrics, None)
        assert norm["token_entropy"] == pytest.approx(1.0)

    def test_max_entropy_no_penalty(self, critic):
        metrics = AestheticMetrics(
            entropy=8.0, compression_ratio=0.5, birkhoff_measure=0.5,
            raw_bytes=100, compressed_bytes=50,
        )
        norm = critic._normalize_dimensions(metrics, None)
        assert norm["token_entropy"] == pytest.approx(0.0)

    def test_midpoint_entropy(self, critic):
        metrics = AestheticMetrics(
            entropy=4.0, compression_ratio=0.5, birkhoff_measure=0.5,
            raw_bytes=100, compressed_bytes=50,
        )
        norm = critic._normalize_dimensions(metrics, None)
        assert norm["token_entropy"] == pytest.approx(0.5)

    def test_high_entropy_low_penalty(self, critic):
        metrics = AestheticMetrics(
            entropy=6.5, compression_ratio=0.5, birkhoff_measure=0.5,
            raw_bytes=100, compressed_bytes=50,
        )
        norm = critic._normalize_dimensions(metrics, None)
        assert norm["token_entropy"] == pytest.approx(0.1875)

    def test_low_entropy_high_penalty(self, critic):
        metrics = AestheticMetrics(
            entropy=1.0, compression_ratio=0.5, birkhoff_measure=0.5,
            raw_bytes=100, compressed_bytes=50,
        )
        norm = critic._normalize_dimensions(metrics, None)
        assert norm["token_entropy"] == pytest.approx(0.875)


class TestCompressionStructurePolarity:
    """High Birkhoff = compressible = repetitive = high penalty."""

    def test_zero_birkhoff_no_penalty(self, critic):
        metrics = AestheticMetrics(
            entropy=4.0, compression_ratio=0.5, birkhoff_measure=0.0,
            raw_bytes=100, compressed_bytes=50,
        )
        norm = critic._normalize_dimensions(metrics, None)
        assert norm["compression_structure"] == pytest.approx(0.0)

    def test_max_birkhoff_max_penalty(self, critic):
        metrics = AestheticMetrics(
            entropy=4.0, compression_ratio=0.5, birkhoff_measure=1.0,
            raw_bytes=100, compressed_bytes=50,
        )
        norm = critic._normalize_dimensions(metrics, None)
        assert norm["compression_structure"] == pytest.approx(1.0)

    def test_high_birkhoff_high_penalty(self, critic):
        metrics = AestheticMetrics(
            entropy=4.0, compression_ratio=0.5, birkhoff_measure=0.85,
            raw_bytes=100, compressed_bytes=50,
        )
        norm = critic._normalize_dimensions(metrics, None)
        assert norm["compression_structure"] == pytest.approx(0.85)


class TestDriftAlignmentUnchanged:
    """Drift and alignment polarity unchanged by 013."""

    def test_drift_normalized_with_sigma(self, critic):
        import numpy as np
        from eigenhelm.models import ProjectionResult

        proj = ProjectionResult(
            coordinates=np.zeros(3), l_drift=0.5, l_virtue=0.3,
            quality_flag="nominal",
        )
        metrics = AestheticMetrics(
            entropy=4.0, compression_ratio=0.5, birkhoff_measure=0.5,
            raw_bytes=100, compressed_bytes=50,
        )
        norm = critic._normalize_dimensions(metrics, proj)
        assert norm["manifold_drift"] == pytest.approx(0.5)
        assert norm["manifold_alignment"] == pytest.approx(0.3)

    def test_no_projection_zero(self, critic):
        metrics = AestheticMetrics(
            entropy=4.0, compression_ratio=0.5, birkhoff_measure=0.5,
            raw_bytes=100, compressed_bytes=50,
        )
        norm = critic._normalize_dimensions(metrics, None)
        assert norm["manifold_drift"] == 0.0
        assert norm["manifold_alignment"] == 0.0


class TestWeightConfigurations:
    """Weight sums and structural bias (013 reweighting)."""

    def test_5dim_weights_sum_to_1(self):
        import numpy as np
        from eigenhelm.models import ProjectionResult

        proj = ProjectionResult(
            coordinates=np.zeros(3), l_drift=0.1, l_virtue=0.1,
            quality_flag="nominal",
        )
        critic = AestheticCritic(exemplars=[b"x" * 100])
        weights = critic._select_weights(proj)
        assert abs(sum(weights.values()) - 1.0) < 1e-9

    def test_4dim_weights_sum_to_1(self):
        import numpy as np
        from eigenhelm.models import ProjectionResult

        proj = ProjectionResult(
            coordinates=np.zeros(3), l_drift=0.1, l_virtue=0.1,
            quality_flag="nominal",
        )
        critic = AestheticCritic()
        weights = critic._select_weights(proj)
        assert abs(sum(weights.values()) - 1.0) < 1e-9

    def test_3dim_weights_sum_to_1(self):
        critic = AestheticCritic(exemplars=[b"x" * 100])
        weights = critic._select_weights(None)
        assert abs(sum(weights.values()) - 1.0) < 1e-9

    def test_2dim_weights_sum_to_1(self):
        critic = AestheticCritic()
        weights = critic._select_weights(None)
        assert abs(sum(weights.values()) - 1.0) < 1e-9

    def test_structural_dims_weighted_higher_than_surface(self):
        import numpy as np
        from eigenhelm.models import ProjectionResult

        proj = ProjectionResult(
            coordinates=np.zeros(3), l_drift=0.1, l_virtue=0.1,
            quality_flag="nominal",
        )
        critic = AestheticCritic()
        weights = critic._select_weights(proj)
        structural = weights["manifold_drift"] + weights["manifold_alignment"]
        surface = weights["token_entropy"] + weights["compression_structure"]
        assert structural > surface

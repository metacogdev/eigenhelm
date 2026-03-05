"""Contract tests for IDynamicHelm construction — invariants 16–17.

Invariants tested:
  16. reject_threshold > accept_threshold enforced at construction (ValueError).
  17. PIDConfig validation at construction (ValueError for invalid values).
"""

from __future__ import annotations

import pytest
from eigenhelm.helm import DynamicHelm, PIDConfig

# ---------------------------------------------------------------------------
# Invariant 16: reject_threshold > accept_threshold
# ---------------------------------------------------------------------------


class TestThresholdValidation:
    def test_reject_greater_than_accept_valid(self):
        helm = DynamicHelm(accept_threshold=0.3, reject_threshold=0.7)
        assert helm is not None

    def test_reject_equals_accept_raises(self):
        with pytest.raises(ValueError):
            DynamicHelm(accept_threshold=0.5, reject_threshold=0.5)

    def test_reject_less_than_accept_raises(self):
        with pytest.raises(ValueError):
            DynamicHelm(accept_threshold=0.7, reject_threshold=0.3)

    def test_default_thresholds_valid(self):
        helm = DynamicHelm()
        assert helm is not None

    def test_thresholds_at_extremes_valid(self):
        helm = DynamicHelm(accept_threshold=0.0, reject_threshold=1.0)
        assert helm is not None

    def test_narrow_band_valid(self):
        helm = DynamicHelm(accept_threshold=0.49, reject_threshold=0.51)
        assert helm is not None


# ---------------------------------------------------------------------------
# Invariant 17: PIDConfig validation
# ---------------------------------------------------------------------------


class TestPIDConfigValidation:
    def test_negative_kp_raises(self):
        with pytest.raises(ValueError):
            PIDConfig(kp=-0.1)

    def test_negative_ki_raises(self):
        with pytest.raises(ValueError):
            PIDConfig(ki=-0.1)

    def test_negative_kd_raises(self):
        with pytest.raises(ValueError):
            PIDConfig(kd=-0.1)

    def test_alpha_zero_raises(self):
        with pytest.raises(ValueError):
            PIDConfig(alpha=0.0)

    def test_alpha_above_one_raises(self):
        with pytest.raises(ValueError):
            PIDConfig(alpha=1.1)

    def test_alpha_one_valid(self):
        config = PIDConfig(alpha=1.0)
        assert config.alpha == 1.0

    def test_negative_i_max_raises(self):
        with pytest.raises(ValueError):
            PIDConfig(i_max=-1.0)

    def test_i_max_zero_valid(self):
        config = PIDConfig(i_max=0.0)
        assert config.i_max == 0.0

    def test_tau_min_gte_tau_max_raises(self):
        with pytest.raises(ValueError):
            PIDConfig(tau_min=1.0, tau_max=0.5)

    def test_tau_min_equals_tau_max_raises(self):
        with pytest.raises(ValueError):
            PIDConfig(tau_min=0.5, tau_max=0.5)

    def test_p_min_gte_p_max_raises(self):
        with pytest.raises(ValueError):
            PIDConfig(p_min=0.9, p_max=0.5)

    def test_negative_gamma_tau_raises(self):
        with pytest.raises(ValueError):
            PIDConfig(gamma_tau=-0.1)

    def test_negative_gamma_p_raises(self):
        with pytest.raises(ValueError):
            PIDConfig(gamma_p=-0.1)

    def test_zero_gains_valid(self):
        """All-zero gains is a legal degenerate configuration."""
        config = PIDConfig(kp=0.0, ki=0.0, kd=0.0)
        assert config.kp == 0.0
        assert config.ki == 0.0
        assert config.kd == 0.0

    def test_default_config_valid(self):
        config = PIDConfig()
        assert config is not None

    def test_pid_config_passed_to_helm(self):
        """DynamicHelm accepts valid PIDConfig."""
        config = PIDConfig(kp=0.5, ki=0.1, kd=0.2)
        helm = DynamicHelm(pid_config=config)
        assert helm is not None

"""Unit tests for Tier B steer() behavior.

Tests:
  - High-entropy input → lowered τ (high error → negative correction).
  - Low-entropy input → raised τ (low error → less correction).
  - Out-of-range input tau/p clamped before PID.
  - create_session() returns zeroed state.
"""

from __future__ import annotations

import os

import pytest
from eigenhelm.helm import DynamicHelm, PIDConfig, SteeringRequest

CLEAN_SOURCE = "x = 1\n" * 3

# Near-random source: high entropy, high aesthetic loss
_raw = os.urandom(300)
HIGH_ENTROPY_SOURCE = "".join(chr(0x21 + (b % 94)) for b in _raw) + "\n"


@pytest.fixture
def helm() -> DynamicHelm:
    return DynamicHelm()


class TestSteerBehavior:
    def test_create_session_zeroed_state(self, helm):
        session = helm.create_session()
        assert session.integral == 0.0
        assert session.prev_error == 0.0
        assert session.filtered_error == 0.0
        assert session.step == 0

    def test_high_entropy_lowers_tau(self, helm):
        """High-entropy input has high loss → PID decreases τ."""
        session = helm.create_session()
        tau_start = 0.8
        req = SteeringRequest(
            source=HIGH_ENTROPY_SOURCE, language="python", tau=tau_start, p=0.9, session=session
        )
        r = helm.steer(req)
        # High error → positive u_k → τ decreases (or stays at tau_min)
        assert r.tau <= tau_start or r.tau == helm._pid_config.tau_min

    def test_zero_error_no_change(self, helm):
        """Empty source (error=0) → no actuation, parameters near initial."""
        session = helm.create_session()
        tau_start = 0.8
        p_start = 0.9
        req = SteeringRequest(
            source="", language="python", tau=tau_start, p=p_start, session=session
        )
        r = helm.steer(req)
        # With zero error and zero integral, u_k=0 → tau and p unchanged
        assert abs(r.tau - tau_start) < 1e-9
        assert abs(r.p - p_start) < 1e-9

    def test_out_of_range_tau_clamped(self, helm):
        session = helm.create_session()
        req = SteeringRequest(
            source=CLEAN_SOURCE, language="python", tau=999.0, p=0.9, session=session
        )
        r = helm.steer(req)
        cfg = helm._pid_config
        assert cfg.tau_min <= r.tau <= cfg.tau_max

    def test_out_of_range_p_clamped(self, helm):
        session = helm.create_session()
        req = SteeringRequest(
            source=CLEAN_SOURCE, language="python", tau=0.8, p=-5.0, session=session
        )
        r = helm.steer(req)
        cfg = helm._pid_config
        assert cfg.p_min <= r.p <= cfg.p_max

    def test_response_has_error_field(self, helm):
        """SteeringResponse.error is the aesthetic loss."""
        session = helm.create_session()
        req = SteeringRequest(
            source=CLEAN_SOURCE, language="python", tau=0.8, p=0.9, session=session
        )
        r = helm.steer(req)
        assert 0.0 <= r.error <= 1.0

    def test_response_has_control_output_field(self, helm):
        """SteeringResponse.control_output is the PID u_k."""
        session = helm.create_session()
        req = SteeringRequest(
            source=CLEAN_SOURCE, language="python", tau=0.8, p=0.9, session=session
        )
        r = helm.steer(req)
        assert isinstance(r.control_output, float)

    def test_step_field_in_response(self, helm):
        """SteeringResponse.step matches session.step after update."""
        session = helm.create_session()
        req = SteeringRequest(
            source=CLEAN_SOURCE, language="python", tau=0.8, p=0.9, session=session
        )
        r = helm.steer(req)
        assert r.step == 1
        assert session.step == 1

    def test_multiple_steps_accumulate(self, helm):
        """Multiple steer() calls accumulate step count correctly."""
        session = helm.create_session()
        tau, p = 0.8, 0.9
        for expected_step in range(1, 6):
            req = SteeringRequest(
                source=CLEAN_SOURCE, language="python", tau=tau, p=p, session=session
            )
            r = helm.steer(req)
            assert r.step == expected_step
            tau, p = r.tau, r.p


class TestCustomPIDConfig:
    def test_zero_gains_no_actuation(self):
        """All-zero PID gains → no actuation → parameters unchanged."""
        helm = DynamicHelm(pid_config=PIDConfig(kp=0.0, ki=0.0, kd=0.0))
        session = helm.create_session()
        tau_start, p_start = 0.8, 0.9
        req = SteeringRequest(
            source=CLEAN_SOURCE, language="python", tau=tau_start, p=p_start, session=session
        )
        r = helm.steer(req)
        assert abs(r.tau - tau_start) < 1e-9
        assert abs(r.p - p_start) < 1e-9

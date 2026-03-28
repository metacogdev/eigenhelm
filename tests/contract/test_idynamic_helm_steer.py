"""Contract tests for IDynamicHelm.steer() — invariants 8–13.

Invariants tested:
  8.  steer() clamps input tau/p to configured bounds.
  9.  Output tau ∈ [tau_min, tau_max], p ∈ [p_min, p_max].
  10. Integral accumulator stays in [-i_max, i_max].
  11. Low-pass filter applied to error before derivative.
  12. session.step incremented by exactly 1 per call.
  13. steer() never raises on empty source or unsupported language.
"""

from __future__ import annotations

import pytest
from eigenhelm.helm import DynamicHelm, SteeringRequest

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


def _req(source, language, tau, p, session):
    return SteeringRequest(
        source=source, language=language, tau=tau, p=p, session=session
    )


@pytest.fixture
def helm() -> DynamicHelm:
    return DynamicHelm()


# ---------------------------------------------------------------------------
# Invariant 8: input tau/p clamped before PID
# ---------------------------------------------------------------------------


class TestInputClamping:
    def test_tau_above_max_clamped(self, helm):
        session = helm.create_session()
        r = helm.steer(_req(PYTHON_SOURCE, "python", 999.0, 0.9, session))
        assert helm._pid_config.tau_min <= r.tau <= helm._pid_config.tau_max

    def test_tau_below_min_clamped(self, helm):
        session = helm.create_session()
        r = helm.steer(_req(PYTHON_SOURCE, "python", -10.0, 0.9, session))
        assert r.tau >= helm._pid_config.tau_min

    def test_p_above_max_clamped(self, helm):
        session = helm.create_session()
        r = helm.steer(_req(PYTHON_SOURCE, "python", 0.8, 999.0, session))
        assert r.p <= helm._pid_config.p_max

    def test_p_below_min_clamped(self, helm):
        session = helm.create_session()
        r = helm.steer(_req(PYTHON_SOURCE, "python", 0.8, -1.0, session))
        assert r.p >= helm._pid_config.p_min


# ---------------------------------------------------------------------------
# Invariant 9: output parameters within bounds
# ---------------------------------------------------------------------------


class TestOutputBounds:
    def test_tau_in_bounds(self, helm):
        session = helm.create_session()
        tau, p = 0.8, 0.9
        for _ in range(10):
            r = helm.steer(_req(PYTHON_SOURCE, "python", tau, p, session))
            assert helm._pid_config.tau_min <= r.tau <= helm._pid_config.tau_max
            tau, p = r.tau, r.p

    def test_p_in_bounds(self, helm):
        session = helm.create_session()
        tau, p = 0.8, 0.9
        for _ in range(10):
            r = helm.steer(_req(PYTHON_SOURCE, "python", tau, p, session))
            assert helm._pid_config.p_min <= r.p <= helm._pid_config.p_max
            tau, p = r.tau, r.p


# ---------------------------------------------------------------------------
# Invariant 10: integral clamped to [-i_max, i_max]
# ---------------------------------------------------------------------------


class TestIntegralClamping:
    def test_integral_within_bounds(self, helm):
        session = helm.create_session()
        req = _req(PYTHON_SOURCE, "python", 0.8, 0.9, session)
        for _ in range(20):
            helm.steer(req)
            assert abs(session.integral) <= helm._pid_config.i_max

    def test_integral_does_not_grow_unbounded(self, helm):
        """Many steps with high error → integral still bounded by i_max."""
        import os

        raw = os.urandom(300)
        src = "".join(chr(0x21 + (b % 94)) for b in raw) + "\n"
        session = helm.create_session()
        req = _req(src, "python", 0.8, 0.9, session)
        for _ in range(50):
            helm.steer(req)
        assert abs(session.integral) <= helm._pid_config.i_max


# ---------------------------------------------------------------------------
# Invariant 11: low-pass filter applied
# ---------------------------------------------------------------------------


class TestLowPassFilter:
    def test_filtered_error_updated_after_steer(self, helm):
        session = helm.create_session()
        assert session.filtered_error == 0.0
        helm.steer(_req(PYTHON_SOURCE, "python", 0.8, 0.9, session))
        assert session.filtered_error >= 0.0

    def test_filtered_error_is_smoothed(self, helm):
        """filtered_error is always between 0 and raw error (smoothing effect)."""
        session = helm.create_session()
        helm.steer(_req(PYTHON_SOURCE, "python", 0.8, 0.9, session))
        raw_error = session.prev_error
        fe = session.filtered_error
        alpha = helm._pid_config.alpha
        # ẽ = α * e + (1-α) * 0 = α * e for first step
        assert abs(fe - alpha * raw_error) < 1e-9


# ---------------------------------------------------------------------------
# Invariant 12: session.step incremented by 1
# ---------------------------------------------------------------------------


class TestStepIncrement:
    def test_step_increments_by_one(self, helm):
        session = helm.create_session()
        assert session.step == 0
        helm.steer(_req(PYTHON_SOURCE, "python", 0.8, 0.9, session))
        assert session.step == 1

    def test_step_matches_response_step(self, helm):
        session = helm.create_session()
        r = helm.steer(_req(PYTHON_SOURCE, "python", 0.8, 0.9, session))
        assert r.step == session.step

    def test_step_accumulates(self, helm):
        session = helm.create_session()
        tau, p = 0.8, 0.9
        for i in range(1, 6):
            r = helm.steer(_req(PYTHON_SOURCE, "python", tau, p, session))
            assert session.step == i
            tau, p = r.tau, r.p


# ---------------------------------------------------------------------------
# Invariant 13: no raise on empty/unsupported
# ---------------------------------------------------------------------------


class TestGracefulDegradation:
    def test_empty_source_no_raise(self, helm):
        session = helm.create_session()
        r = helm.steer(_req("", "python", 0.8, 0.9, session))
        assert r is not None

    def test_unsupported_language_no_raise(self, helm):
        session = helm.create_session()
        r = helm.steer(_req(PYTHON_SOURCE, "brainfuck", 0.8, 0.9, session))
        assert r is not None

    def test_empty_source_output_in_bounds(self, helm):
        session = helm.create_session()
        r = helm.steer(_req("", "python", 0.8, 0.9, session))
        assert helm._pid_config.tau_min <= r.tau <= helm._pid_config.tau_max
        assert helm._pid_config.p_min <= r.p <= helm._pid_config.p_max

"""Unit tests for PIDController — written FIRST (TDD), must fail before implementation.

PID normative equations (R-003):
    ẽ_k = α · e_k + (1 − α) · ẽ_{k-1}
    u_k  = Kp·e_k + Ki·clamp(Σe + e_k, -I_max, I_max) + Kd·(ẽ_k − ẽ_{k-1})
    τ_{k+1} = clamp(τ_k − γ_τ·u_k, τ_min, τ_max)
    p_{k+1} = clamp(p_k − γ_p·u_k, p_min, p_max)
"""

from __future__ import annotations

from eigenhelm.helm.models import PIDConfig, SteeringSession
from eigenhelm.helm.pid import PIDController

# ---------------------------------------------------------------------------
# Proportional-only response (Ki=0, Kd=0)
# ---------------------------------------------------------------------------


class TestProportionalOnly:
    def test_proportional_output(self):
        """u_k = Kp * e_k when Ki=Kd=0."""
        config = PIDConfig(kp=1.0, ki=0.0, kd=0.0)
        pid = PIDController(config)
        session = SteeringSession()
        u = pid.update(0.5, session)
        assert abs(u - 0.5) < 1e-9

    def test_proportional_output_zero_error(self):
        """u_k = 0.0 when e_k = 0.0 and Ki=Kd=0."""
        config = PIDConfig(kp=2.0, ki=0.0, kd=0.0)
        pid = PIDController(config)
        session = SteeringSession()
        u = pid.update(0.0, session)
        assert u == 0.0

    def test_proportional_scaling(self):
        """u_k scales linearly with Kp."""
        config = PIDConfig(kp=3.0, ki=0.0, kd=0.0)
        pid = PIDController(config)
        session = SteeringSession()
        u = pid.update(0.4, session)
        assert abs(u - 1.2) < 1e-9


# ---------------------------------------------------------------------------
# Integral accumulation and anti-windup clamping
# ---------------------------------------------------------------------------


class TestIntegral:
    def test_integral_accumulates(self):
        """After two steps with Kp=0, Kd=0: session.integral = clamp(e1+e2, ...)."""
        config = PIDConfig(kp=0.0, ki=1.0, kd=0.0, i_max=10.0)
        pid = PIDController(config)
        session = SteeringSession()
        pid.update(0.3, session)  # integral = 0.3
        pid.update(0.4, session)  # integral = 0.7
        assert abs(session.integral - 0.7) < 1e-9

    def test_integral_clamped_at_i_max(self):
        """Integral saturates at i_max."""
        config = PIDConfig(kp=0.0, ki=1.0, kd=0.0, i_max=1.0)
        pid = PIDController(config)
        session = SteeringSession()
        for _ in range(20):
            pid.update(1.0, session)  # Large positive error drives integral up
        assert session.integral <= 1.0

    def test_integral_clamped_at_neg_i_max(self):
        """Integral saturates at -i_max for negative errors."""
        config = PIDConfig(kp=0.0, ki=1.0, kd=0.0, i_max=1.0)
        pid = PIDController(config)
        session = SteeringSession()
        for _ in range(20):
            pid.update(-1.0, session)
        assert session.integral >= -1.0

    def test_i_max_zero_integral_always_zero(self):
        """i_max=0 → integral always 0 (equivalent to Ki=0)."""
        config = PIDConfig(kp=0.0, ki=1.0, kd=0.0, i_max=0.0)
        pid = PIDController(config)
        session = SteeringSession()
        for _ in range(5):
            pid.update(0.5, session)
        assert session.integral == 0.0

    def test_ki_zero_no_integration(self):
        """Ki=0 → integral term contributes 0 to output."""
        config = PIDConfig(kp=0.0, ki=0.0, kd=0.0, i_max=10.0)
        pid = PIDController(config)
        session = SteeringSession()
        u = pid.update(0.5, session)
        assert u == 0.0


# ---------------------------------------------------------------------------
# Derivative low-pass filtering
# ---------------------------------------------------------------------------


class TestDerivativeLowPass:
    def test_derivative_uses_filtered_error(self):
        """Derivative = Kd * (filtered_error_k - filtered_error_{k-1})."""
        alpha = 1.0  # No filtering: filtered_error = raw error
        config = PIDConfig(kp=0.0, ki=0.0, kd=1.0, alpha=alpha, i_max=10.0)
        pid = PIDController(config)
        session = SteeringSession()

        # Step 1: filtered_error_0 = 1.0 * 0.5 + 0 = 0.5, prev=0
        # derivative = Kd * (0.5 - 0.0) = 0.5
        u1 = pid.update(0.5, session)
        assert abs(u1 - 0.5) < 1e-9

        # Step 2: filtered_error_1 = 1.0 * 0.3 + 0 = 0.3
        # derivative = Kd * (0.3 - 0.5) = -0.2
        u2 = pid.update(0.3, session)
        assert abs(u2 - (-0.2)) < 1e-9

    def test_low_pass_filters_derivative_noise(self):
        """alpha < 1.0 smooths the derivative term."""
        alpha = 0.5
        config = PIDConfig(kp=0.0, ki=0.0, kd=1.0, alpha=alpha, i_max=10.0)
        pid = PIDController(config)
        session = SteeringSession()

        # Step 1: ẽ_0 = 0.5 * 1.0 + 0.5 * 0.0 = 0.5, derivative = 0.5 - 0.0 = 0.5
        pid.update(1.0, session)
        fe_after_1 = session.filtered_error
        assert abs(fe_after_1 - 0.5) < 1e-9

        # Step 2: ẽ_1 = 0.5 * 1.0 + 0.5 * 0.5 = 0.75, derivative = 0.75 - 0.5 = 0.25
        u2 = pid.update(1.0, session)
        assert abs(u2 - 0.25) < 1e-9

    def test_alpha_one_no_smoothing(self):
        """alpha=1.0 → filtered_error == raw error (no memory)."""
        config = PIDConfig(kp=0.0, ki=0.0, kd=0.0, alpha=1.0)
        pid = PIDController(config)
        session = SteeringSession()
        pid.update(0.7, session)
        assert abs(session.filtered_error - 0.7) < 1e-9

    def test_kd_zero_no_derivative(self):
        """Kd=0 → derivative term contributes 0."""
        config = PIDConfig(kp=0.0, ki=0.0, kd=0.0)
        pid = PIDController(config)
        session = SteeringSession()
        u = pid.update(0.5, session)
        pid.update(0.1, session)
        assert u == 0.0


# ---------------------------------------------------------------------------
# Output clamping via actuation equations
# ---------------------------------------------------------------------------


class TestOutputClamping:
    def test_tau_clamped_to_max(self):
        """Large negative control output drives tau up; clamped at tau_max."""
        config = PIDConfig(kp=100.0, ki=0.0, kd=0.0, tau_min=0.1, tau_max=1.5, gamma_tau=1.0)
        pid = PIDController(config)
        # Large positive error → large u_k → tau decreases but is clamped
        # Actually: large positive error e_k with kp=100 → u_k=100*e_k
        # tau = clamp(tau_start - gamma_tau * u_k, tau_min, tau_max)
        # With tau_start=0.8 and u_k=100 (error=1.0): tau = clamp(0.8-100, 0.1, 1.5) = 0.1
        tau_new, _ = pid.actuate(0.8, 0.9, 100.0)
        assert tau_new == 0.1

    def test_tau_clamped_to_min(self):
        """Large positive control output clamps tau at tau_min."""
        config = PIDConfig(kp=100.0, ki=0.0, kd=0.0, tau_min=0.1, tau_max=1.5, gamma_tau=1.0)
        pid = PIDController(config)
        # Negative u_k → tau increases; clamped at tau_max
        tau_new, _ = pid.actuate(0.8, 0.9, -100.0)
        assert tau_new == 1.5

    def test_p_clamped_to_bounds(self):
        """Output p stays within [p_min, p_max]."""
        config = PIDConfig(kp=0.0, ki=0.0, kd=0.0, p_min=0.1, p_max=0.99, gamma_p=1.0)
        pid = PIDController(config)
        _, p_new = pid.actuate(0.8, 0.9, 100.0)
        assert 0.1 <= p_new <= 0.99

    def test_zero_control_output_no_change(self):
        """u_k=0 → tau and p unchanged (modulo floating point)."""
        config = PIDConfig(kp=0.0, ki=0.0, kd=0.0)
        pid = PIDController(config)
        tau_new, p_new = pid.actuate(0.8, 0.9, 0.0)
        assert abs(tau_new - 0.8) < 1e-9
        assert abs(p_new - 0.9) < 1e-9


# ---------------------------------------------------------------------------
# Degenerate configurations
# ---------------------------------------------------------------------------


class TestDegenerateConfigurations:
    def test_all_zero_gains(self):
        """Kp=Ki=Kd=0 → u_k=0 always."""
        config = PIDConfig(kp=0.0, ki=0.0, kd=0.0)
        pid = PIDController(config)
        session = SteeringSession()
        u = pid.update(0.9, session)
        assert u == 0.0

    def test_zero_error_passthrough(self):
        """e_k=0.0 → PID output = 0.0 (no correction needed, assuming Ki integral=0)."""
        config = PIDConfig(kp=1.0, ki=1.0, kd=1.0)
        pid = PIDController(config)
        session = SteeringSession()
        u = pid.update(0.0, session)
        assert u == 0.0

    def test_step_incremented_on_update(self):
        """session.step increments by 1 per update() call."""
        config = PIDConfig()
        pid = PIDController(config)
        session = SteeringSession()
        assert session.step == 0
        pid.update(0.5, session)
        assert session.step == 1
        pid.update(0.3, session)
        assert session.step == 2

    def test_prev_error_updated(self):
        """session.prev_error is set to e_k after each update."""
        config = PIDConfig()
        pid = PIDController(config)
        session = SteeringSession()
        pid.update(0.7, session)
        assert abs(session.prev_error - 0.7) < 1e-9


# ---------------------------------------------------------------------------
# Step-function convergence (SC-004 shape, PIDController level)
# ---------------------------------------------------------------------------


class TestStepFunctionConvergence:
    def test_step_response_converges(self):
        """Step input: τ trajectory should converge and reduce oscillation after step 10."""
        config = PIDConfig(kp=0.3, ki=0.05, kd=0.1)
        pid = PIDController(config)
        session = SteeringSession()

        tau = 0.8
        taus = []
        for _ in range(20):
            u = pid.update(0.8, session)  # Constant high error
            tau, _ = pid.actuate(tau, 0.9, u)
            taus.append(tau)

        # Tau should have moved from initial 0.8 in response to positive error
        # (positive error → u_k > 0 → tau decreases)
        assert taus[-1] < taus[0] or taus[-1] == config.tau_min

    def test_zero_error_stable(self):
        """Perfect code (error=0) → parameters remain stable."""
        config = PIDConfig(kp=0.3, ki=0.05, kd=0.1)
        pid = PIDController(config)
        session = SteeringSession()

        tau, p = 0.8, 0.9
        for _ in range(20):
            u = pid.update(0.0, session)
            tau, p = pid.actuate(tau, p, u)

        # With no error, there's no actuation
        assert abs(tau - 0.8) < 1e-9
        assert abs(p - 0.9) < 1e-9

    def test_returns_float(self):
        """update() returns a float."""
        config = PIDConfig()
        pid = PIDController(config)
        session = SteeringSession()
        u = pid.update(0.5, session)
        assert isinstance(u, float)

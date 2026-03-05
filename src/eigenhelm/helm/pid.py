"""Discrete PID controller for Tier B inference steering.

Normative equations (R-003):
    ẽ_k = α · e_k + (1 − α) · ẽ_{k-1}                   (low-pass filter)
    u_k  = Kp·e_k + Ki·clamp(Σe + e_k, -I_max, I_max) + Kd·(ẽ_k − ẽ_{k-1})
    τ_{k+1} = clamp(τ_k − γ_τ·u_k, τ_min, τ_max)        (temperature actuation)
    p_{k+1} = clamp(p_k − γ_p·u_k, p_min, p_max)         (top-p actuation)
"""

from __future__ import annotations

from eigenhelm.helm.models import PIDConfig, SteeringSession


class PIDController:
    """Discrete PID controller with low-pass filtered derivative and integral anti-windup."""

    def __init__(self, config: PIDConfig) -> None:
        self._cfg = config

    def update(self, error: float, session: SteeringSession) -> float:
        """Compute PID output u_k and mutate session state.

        Args:
            error: Current error signal e_k ∈ [0.0, 1.0].
            session: Mutable PID state (mutated in-place).

        Returns:
            Control output u_k.
        """
        cfg = self._cfg

        # Low-pass filtered derivative
        filtered = cfg.alpha * error + (1.0 - cfg.alpha) * session.filtered_error

        # Integral with anti-windup clamping
        new_integral = session.integral + error
        if cfg.i_max > 0:
            new_integral = max(-cfg.i_max, min(cfg.i_max, new_integral))
        else:
            new_integral = 0.0

        # PID output
        u = cfg.kp * error + cfg.ki * new_integral + cfg.kd * (filtered - session.filtered_error)

        # Mutate session state
        session.integral = new_integral
        session.prev_error = error
        session.filtered_error = filtered
        session.step += 1

        return u

    def actuate(self, tau: float, p: float, control_output: float) -> tuple[float, float]:
        """Apply actuation equations and clamp outputs to configured bounds.

        Args:
            tau: Current temperature.
            p: Current top-p.
            control_output: PID output u_k.

        Returns:
            (tau_new, p_new) clamped to configured bounds.
        """
        cfg = self._cfg
        tau_new = tau - cfg.gamma_tau * control_output
        tau_new = max(cfg.tau_min, min(cfg.tau_max, tau_new))

        p_new = p - cfg.gamma_p * control_output
        p_new = max(cfg.p_min, min(cfg.p_max, p_new))

        return tau_new, p_new

"""Concrete DynamicHelm — Stage 3 implementation.

Tier A: evaluate() — universal post-hoc evaluation.
Tier B: steer()    — PID-controlled inference parameter steering.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from eigenhelm.critic import AestheticCritic
from eigenhelm.helm.models import (
    EvaluationRequest,
    EvaluationResponse,
    PIDConfig,
    SteeringRequest,
    SteeringResponse,
    SteeringSession,
)
from eigenhelm.helm.pid import PIDController
from eigenhelm.virtue_extractor import VirtueExtractor

if TYPE_CHECKING:
    from eigenhelm.critic import Critique
    from eigenhelm.models import EigenspaceModel

# Warning message catalog (R-010)
_WARN_NO_EIGENSPACE = (
    "No eigenspace model loaded; evaluation uses information-theoretic"
    " metrics only (structural_confidence=low)"
)
_WARN_NO_UNITS = (
    "No extractable code units found; evaluation uses information-theoretic"
    " metrics only (structural_confidence=low)"
)


def _warn_unsupported(lang: str) -> str:
    return (
        f"Unsupported language '{lang}'; evaluation uses information-theoretic"
        " metrics only (structural_confidence=low)"
    )


def _warn_partial_parse(lang: str) -> str:
    return f"Partial parse for language '{lang}'; structural metrics may be degraded"


class DynamicHelm:
    """Stage 3 concrete implementation of IDynamicHelm."""

    def __init__(
        self,
        eigenspace: EigenspaceModel | None = None,
        accept_threshold: float = 0.4,
        reject_threshold: float = 0.6,
        pid_config: PIDConfig | None = None,
    ) -> None:
        if reject_threshold <= accept_threshold:
            raise ValueError(
                f"reject_threshold ({reject_threshold}) must be > "
                f"accept_threshold ({accept_threshold})"
            )
        self._eigenspace = eigenspace
        self._accept_threshold = accept_threshold
        self._reject_threshold = reject_threshold
        self._pid_config = pid_config if pid_config is not None else PIDConfig()
        self._extractor = VirtueExtractor()
        self._critic = AestheticCritic(
            sigma_drift=eigenspace.sigma_drift if eigenspace is not None else 1.0,
            sigma_virtue=eigenspace.sigma_virtue if eigenspace is not None else 1.0,
        )
        self._pid = PIDController(self._pid_config)

    # ------------------------------------------------------------------
    # Internal pipeline (shared by evaluate() and steer())
    # ------------------------------------------------------------------

    def _evaluate_pipeline(
        self, source: str, language: str, file_path: str | None = None
    ) -> tuple[Critique, str | None]:
        """Run Stage 1→2→3 pipeline. Returns (critique, warning_or_None)."""
        from eigenhelm.models import UnsupportedLanguageError

        # Handle empty/whitespace source early
        if not source.strip():
            critique = self._critic.evaluate("", language)
            return critique, None

        # Stage 1: extract
        warning: str | None = None
        projection = None

        try:
            vectors = self._extractor.extract(source, language, file_path=file_path)
        except UnsupportedLanguageError:
            vectors = []
            warning = _warn_unsupported(language)

        # Determine projection and warnings
        if self._eigenspace is not None:
            if vectors:
                projection = self._extractor.project(vectors[0], model=self._eigenspace)
                # Check for partial parse
                if vectors[0].partial_parse:
                    warning = _warn_partial_parse(language)
            else:
                # Eigenspace available but no vectors extracted
                if warning is None:
                    warning = _WARN_NO_UNITS
        else:
            # No eigenspace: always low-confidence
            if warning is None:
                warning = _WARN_NO_EIGENSPACE

        # Stage 2: evaluate
        critique = self._critic.evaluate(source, language, projection=projection)

        return critique, warning

    # ------------------------------------------------------------------
    # Tier A: evaluate()
    # ------------------------------------------------------------------

    def evaluate(self, request: EvaluationRequest) -> EvaluationResponse:
        """Tier A: Evaluate code and return accept/warn/reject decision."""
        critique, warning = self._evaluate_pipeline(
            request.source, request.language, request.file_path
        )

        score = critique.score.value
        decision = self._map_decision(score)

        return EvaluationResponse(
            decision=decision,
            score=score,
            structural_confidence=critique.score.structural_confidence,
            critique=critique,
            warning=warning,
        )

    def _map_decision(self, score: float) -> str:
        """Map aesthetic loss to three-valued decision (R-002).

        Boundary semantics: strict inequalities for accept/reject;
        exact-threshold values → "warn".
        """
        if score < self._accept_threshold:
            return "accept"
        if score > self._reject_threshold:
            return "reject"
        return "warn"

    # ------------------------------------------------------------------
    # Tier B: steer()
    # ------------------------------------------------------------------

    def create_session(self) -> SteeringSession:
        """Create a new SteeringSession with zeroed state."""
        return SteeringSession()

    def steer(self, request: SteeringRequest) -> SteeringResponse:
        """Tier B: Compute updated inference parameters using PID control."""
        cfg = self._pid_config
        session = request.session

        # Clamp input tau/p to configured bounds (R-004)
        tau = max(cfg.tau_min, min(cfg.tau_max, request.tau))
        p = max(cfg.p_min, min(cfg.p_max, request.p))

        # Run evaluation pipeline
        critique, _ = self._evaluate_pipeline(request.source, request.language)
        error = critique.score.value

        # PID update
        u = self._pid.update(error, session)
        tau_new, p_new = self._pid.actuate(tau, p, u)

        return SteeringResponse(
            tau=tau_new,
            p=p_new,
            error=error,
            control_output=u,
            step=session.step,
        )

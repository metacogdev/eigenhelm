"""Stage 3: IDynamicHelm — feedback actuator for code aesthetic governance.

Public API:
    IDynamicHelm   — abstract base class
    DynamicHelm    — concrete implementation
    EvaluationRequest, EvaluationResponse   — Tier A types
    SteeringRequest, SteeringResponse, SteeringSession   — Tier B types
    PIDConfig      — PID controller configuration
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from eigenhelm.helm.models import (
    EvaluationRequest,
    EvaluationResponse,
    PIDConfig,
    SteeringRequest,
    SteeringResponse,
    SteeringSession,
)

__all__ = [
    "IDynamicHelm",
    "DynamicHelm",
    "EvaluationRequest",
    "EvaluationResponse",
    "SteeringRequest",
    "SteeringResponse",
    "SteeringSession",
    "PIDConfig",
]


class IDynamicHelm(ABC):
    """Stage 3 interface: feedback actuator for code aesthetic governance.

    Tier A — Universal post-hoc evaluation. Stateless. Thread-safe.
    Tier B — PID-controlled inference parameter steering. Stateful per-session.
             Thread-safe when concurrent calls use different SteeringSessions.

    Constructor parameters:
        eigenspace: EigenspaceModel | None = None
            Pre-loaded PCA eigenspace model. Caller MUST pre-load via
            eigenhelm.eigenspace.load_model(). DynamicHelm does NOT perform
            file I/O. When None, operates in low-confidence mode.
        accept_threshold: float = 0.4
            Loss below this → "accept" decision.
        reject_threshold: float = 0.6
            Loss above this → "reject" decision.
            Must be > accept_threshold (hysteresis).
        pid_config: PIDConfig = PIDConfig()
            PID controller configuration for Tier B.

    Internal composition:
        DynamicHelm creates VirtueExtractor and AestheticCritic internally.
        The caller provides only source code and language — not pre-extracted
        vectors or projections.

    Internal pipeline (both evaluate() and steer()):
        1. VirtueExtractor.extract(source, language, file_path) → list[FeatureVector]
        2. If eigenspace and vectors non-empty:
              VirtueExtractor.project(vectors[0], eigenspace) → ProjectionResult
        3. IAestheticCritic.evaluate(source, language, projection) → Critique
        4. Map Critique to decision (Tier A) or PID update (Tier B)

    Multi-vector handling:
        When extract() returns multiple FeatureVector objects, uses the first
        vector for projection. Future stages may aggregate.

    Exception handling:
        Catches UnsupportedLanguageError from extract() via try/except, then
        falls back to AestheticCritic.evaluate(source, language, projection=None).
    """

    @abstractmethod
    def evaluate(self, request: EvaluationRequest) -> EvaluationResponse:
        """Tier A: Evaluate a code block and return accept/warn/reject decision.

        Args:
            request: EvaluationRequest with source code and language.

        Returns:
            EvaluationResponse with decision, score, critique, and warnings.

        Contract:
            - MUST NOT raise on empty/whitespace source.
            - MUST NOT raise on unsupported language.
            - MUST return a valid EvaluationResponse in all cases.
            - Empty/whitespace source → decision="accept", score=0.0.
            - Unsupported language → warning set, structural_confidence="low".
            - No eigenspace → warning set, structural_confidence="low".
            - Empty extract result → skip projection, structural_confidence="low".
            - partial_parse=True → warning set, but score/decision unaffected.
        """
        ...

    @abstractmethod
    def steer(self, request: SteeringRequest) -> SteeringResponse:
        """Tier B: Compute updated inference parameters using PID control.

        Evaluates the current code block, computes the error signal,
        updates PID state in request.session, and returns adjusted
        τ and p parameters.

        Args:
            request: SteeringRequest with current code, parameters, and session.

        Returns:
            SteeringResponse with updated τ, p, error, and control output.

        Contract:
            - MUST mutate request.session (integral, prev_error,
              filtered_error, step).
            - MUST clamp input τ/p to configured bounds before PID computation.
            - MUST clamp output τ to [pid_config.tau_min, pid_config.tau_max].
            - MUST clamp output p to [pid_config.p_min, pid_config.p_max].
            - MUST clamp integral to [-pid_config.i_max, pid_config.i_max].
            - MUST apply low-pass filter before derivative computation.
            - MUST NOT raise on empty source or unsupported language.
        """
        ...

    @abstractmethod
    def create_session(self) -> SteeringSession:
        """Create a new SteeringSession with zeroed state.

        Returns:
            Fresh SteeringSession ready for use with steer().
        """
        ...


# Deferred import: DynamicHelm depends on eigenhelm.helm.dynamic_helm
# (created in Phase 3). Import at bottom to avoid circular reference.
from eigenhelm.helm.dynamic_helm import DynamicHelm  # noqa: E402, F401

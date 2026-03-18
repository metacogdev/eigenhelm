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
    from eigenhelm.models import EigenspaceModel, FeatureVector, ProjectionResult

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

    # Hardcoded fallback thresholds (pre-015 behavior)
    _DEFAULT_ACCEPT = 0.4
    _DEFAULT_REJECT = 0.6

    def __init__(
        self,
        eigenspace: EigenspaceModel | None = None,
        accept_threshold: float | None = None,
        reject_threshold: float | None = None,
        pid_config: PIDConfig | None = None,
    ) -> None:
        # 015: Resolve thresholds — caller explicit > model calibration > hardcoded
        if accept_threshold is not None:
            resolved_accept = accept_threshold
        elif eigenspace is not None and eigenspace.calibrated_accept is not None:
            resolved_accept = eigenspace.calibrated_accept
        else:
            resolved_accept = self._DEFAULT_ACCEPT

        if reject_threshold is not None:
            resolved_reject = reject_threshold
        elif eigenspace is not None and eigenspace.calibrated_reject is not None:
            resolved_reject = eigenspace.calibrated_reject
        else:
            resolved_reject = self._DEFAULT_REJECT

        if resolved_reject <= resolved_accept:
            raise ValueError(
                f"reject_threshold ({resolved_reject}) must be > "
                f"accept_threshold ({resolved_accept})"
            )
        self._eigenspace = eigenspace
        self._accept_threshold = resolved_accept
        self._reject_threshold = resolved_reject
        self._pid_config = pid_config if pid_config is not None else PIDConfig()
        self._extractor = VirtueExtractor()

        # Decompress exemplar bytes from model for NCD computation (010)
        exemplar_bytes = None
        exemplar_ids = None
        if eigenspace is not None and eigenspace.exemplars is not None:
            import zlib as _zlib

            exemplar_bytes = [
                _zlib.decompress(e.compressed_content) for e in eigenspace.exemplars
            ]
            exemplar_ids = [e.content_hash for e in eigenspace.exemplars]

        self._critic = AestheticCritic(
            sigma_drift=eigenspace.sigma_drift if eigenspace is not None else 1.0,
            sigma_virtue=eigenspace.sigma_virtue if eigenspace is not None else 1.0,
            reject_threshold=resolved_reject,
            marginal_threshold=resolved_accept,
            exemplars=exemplar_bytes,
            exemplar_ids=exemplar_ids,
        )
        self._pid = PIDController(self._pid_config)

    # ------------------------------------------------------------------
    # Internal pipeline (shared by evaluate() and steer())
    # ------------------------------------------------------------------

    def _evaluate_pipeline(
        self, source: str, language: str, file_path: str | None = None
    ) -> tuple[Critique, str | None, ProjectionResult | None, list[FeatureVector]]:
        """Run Stage 1→2→3 pipeline.

        Returns (critique, warning_or_None, projection, vectors).
        """
        from eigenhelm.models import UnsupportedLanguageError

        # Handle empty/whitespace source early
        if not source.strip():
            critique = self._critic.evaluate("", language)
            return critique, None, None, []

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

        # Stage 2: evaluate (pass feature vector for anti-pattern detection)
        fv_values = vectors[0].values if vectors else None
        critique = self._critic.evaluate(
            source, language, projection=projection, feature_vector=fv_values
        )

        return critique, warning, projection, vectors

    # ------------------------------------------------------------------
    # Tier A: evaluate()
    # ------------------------------------------------------------------

    def evaluate(self, request: EvaluationRequest) -> EvaluationResponse:
        """Tier A: Evaluate code and return accept/warn/reject decision."""
        from eigenhelm.attribution import compute_attribution
        from eigenhelm.output.percentile import DimensionContribution, compute_quality_percentile

        critique, warning, projection, vectors = self._evaluate_pipeline(
            request.source, request.language, request.file_path
        )

        score = critique.score.value
        decision = self._map_decision(score)

        # 016: Compute quality percentile from model's score distribution
        distribution = (
            self._eigenspace.score_distribution
            if self._eigenspace is not None
            else None
        )
        pct_result = compute_quality_percentile(score, distribution)

        # 016: Extract per-dimension contributions from AestheticScore
        contributions = tuple(
            DimensionContribution(
                dimension=dim,
                normalized_value=critique.score.normalized_values.get(dim, 0.0),
                weight=critique.score.weights.get(dim, 0.0),
                weighted_contribution=critique.score.contributions.get(dim, 0.0),
            )
            for dim in critique.score.weights
        )

        # 017: Compute score attribution
        feature_vector = vectors[0] if vectors else None
        attribution = compute_attribution(
            metrics=critique.metrics,
            normalized_values=critique.score.normalized_values,
            projection=projection,
            model=self._eigenspace,
            feature_vector=feature_vector,
            nearest_exemplar_id=critique.nearest_exemplar_id,
            source=request.source,
            file_path=request.file_path,
            top_n=request.top_n,
            directive_threshold=request.directive_threshold,
        )

        return EvaluationResponse(
            decision=decision,
            score=score,
            structural_confidence=critique.score.structural_confidence,
            critique=critique,
            warning=warning,
            percentile=pct_result.percentile if pct_result.available else None,
            percentile_available=pct_result.available,
            contributions=contributions,
            attribution=attribution,
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
        critique, _, _, _ = self._evaluate_pipeline(request.source, request.language)
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

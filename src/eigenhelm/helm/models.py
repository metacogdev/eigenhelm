"""Stage 3 data types for IDynamicHelm."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from eigenhelm.attribution.models import AttributionResult
    from eigenhelm.critic import Critique
    from eigenhelm.output.percentile import DimensionContribution


@dataclass(frozen=True)
class EvaluationRequest:
    """Input to Tier A evaluate()."""

    source: str
    language: str  # Canonical lowercase key from language_map.LANGUAGE_MAP
    file_path: str | None = None  # Passed through to VirtueExtractor.extract()
    top_n: int = 3  # 017: top features per PCA dimension in attribution
    directive_threshold: float = 0.3  # 017: minimum normalized score for directives

    def __post_init__(self) -> None:
        if self.top_n < 1:
            raise ValueError(f"top_n must be >= 1, got {self.top_n}")
        if not (0.0 <= self.directive_threshold <= 1.0):
            raise ValueError(
                f"directive_threshold must be in [0.0, 1.0], got {self.directive_threshold}"
            )


@dataclass(frozen=True)
class EvaluationResponse:
    """Output from Tier A evaluate()."""

    decision: Literal["accept", "warn", "reject"]
    score: float  # Aesthetic loss ∈ [0.0, 1.0] — always critique.score.value
    structural_confidence: Literal["high", "low"]  # Always critique.score.structural_confidence
    critique: Critique  # Full Stage 2 output
    warning: str | None = None  # Machine-parseable warning per R-010
    percentile: float | None = None  # Quality percentile 0-100 (higher = better), None if unavailable
    percentile_available: bool = False  # True when model has ScoreDistribution
    contributions: tuple[DimensionContribution, ...] = ()  # Per-dimension breakdown (016)
    attribution: AttributionResult | None = None  # Score attribution (017)


@dataclass
class SteeringSession:
    """Mutable PID state for one generation session.

    Lifecycle:
    - Created via create_session() with zeroed state.
    - Passed into steer() on each step; mutated in-place.
    - MUST NOT be reused across different generation tasks.
    - MUST NOT be shared across threads (caller-owned).
    - O(1) memory: four floats and an int. No unbounded growth.
    """

    integral: float = 0.0
    prev_error: float = 0.0
    filtered_error: float = 0.0
    step: int = 0


@dataclass(frozen=True)
class SteeringRequest:
    """Input to Tier B steer()."""

    source: str
    language: str
    tau: float  # Current temperature (clamped to bounds before PID)
    p: float  # Current top-p (clamped to bounds before PID)
    session: SteeringSession


@dataclass(frozen=True)
class SteeringResponse:
    """Output from Tier B steer()."""

    tau: float  # Updated temperature
    p: float  # Updated top-p
    error: float  # Raw error e_k
    control_output: float  # PID output u_k
    step: int  # Step index after update


@dataclass(frozen=True)
class PIDConfig:
    """PID controller configuration (set once at DynamicHelm construction).

    All gains ≥ 0, alpha ∈ (0, 1], i_max ≥ 0,
    tau_min < tau_max, p_min < p_max, learning rates ≥ 0.
    Violation raises ValueError.
    """

    kp: float = 0.3
    ki: float = 0.05
    kd: float = 0.1
    alpha: float = 0.2  # Low-pass filter coefficient ∈ (0, 1]
    i_max: float = 5.0  # Integral anti-windup bound (≥ 0)
    tau_min: float = 0.1
    tau_max: float = 1.5
    p_min: float = 0.1
    p_max: float = 0.99
    gamma_tau: float = 0.1  # Temperature learning rate
    gamma_p: float = 0.05  # Top-p learning rate

    def __post_init__(self) -> None:
        if self.kp < 0:
            raise ValueError(f"kp must be ≥ 0, got {self.kp}")
        if self.ki < 0:
            raise ValueError(f"ki must be ≥ 0, got {self.ki}")
        if self.kd < 0:
            raise ValueError(f"kd must be ≥ 0, got {self.kd}")
        if not (0 < self.alpha <= 1):
            raise ValueError(f"alpha must be in (0, 1], got {self.alpha}")
        if self.i_max < 0:
            raise ValueError(f"i_max must be ≥ 0, got {self.i_max}")
        if self.tau_min >= self.tau_max:
            raise ValueError(f"tau_min must be < tau_max, got {self.tau_min} >= {self.tau_max}")
        if self.p_min >= self.p_max:
            raise ValueError(f"p_min must be < p_max, got {self.p_min} >= {self.p_max}")
        if self.gamma_tau < 0:
            raise ValueError(f"gamma_tau must be ≥ 0, got {self.gamma_tau}")
        if self.gamma_p < 0:
            raise ValueError(f"gamma_p must be ≥ 0, got {self.gamma_p}")

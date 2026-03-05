"""Stage 2 — IAestheticCritic: information-theoretic code aesthetic evaluation.

Exports:
    IAestheticCritic  — abstract base class
    AestheticCritic   — concrete implementation
    AestheticMetrics  — raw metric values
    AestheticScore    — scalar weighted loss + metadata
    Violation         — per-dimension penalty contribution
    Critique          — full structured evaluation output
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from eigenhelm.models import ProjectionResult


# ---------------------------------------------------------------------------
# Frozen dataclasses — Stage 2 vocabulary
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AestheticMetrics:
    """Raw information-theoretic metric values for one source string.

    entropy         — Shannon H(P) in bits/byte, range [0.0, 8.0]
    compression_ratio — zlib_size / raw_size; None when raw_bytes <
                        min_compression_bytes (avoids framing overhead distortion)
    birkhoff_measure — M_Z = (N·H - K) / (N·H), clamped [0.0, 1.0];
                        0.0 when compression_ratio is None
    raw_bytes       — len(source.encode("utf-8")); always populated
    compressed_bytes — len(zlib.compress(source_bytes)); always populated

    Reference: Birkhoff (1933); Rigau et al. (2008) IEEE CG&A.
    """

    entropy: float
    compression_ratio: float | None
    birkhoff_measure: float
    raw_bytes: int
    compressed_bytes: int


@dataclass(frozen=True)
class Violation:
    """A single dimension contributing to the aesthetic penalty.

    dimension  — canonical key (one of four allowed string literals)
    raw_value  — original metric value before normalization
    normalized_value — value normalized to [0, 1]
    contribution     — share of total loss: (norm_val * weight) / total_loss
    """

    dimension: Literal[
        "manifold_drift",
        "manifold_alignment",
        "token_entropy",
        "compression_structure",
    ]
    raw_value: float
    normalized_value: float
    contribution: float


@dataclass(frozen=True)
class AestheticScore:
    """Scalar aesthetic loss + confidence metadata.

    value                — loss ∈ [0.0, 1.0]. Lower is better (0 = ideal).
    structural_confidence — "high" when projection provided; "low" otherwise
    weights              — effective per-dimension weights summing to 1.0
    """

    value: float
    structural_confidence: Literal["high", "low"]
    weights: dict[str, float]


@dataclass(frozen=True)
class Critique:
    """Full structured output from IAestheticCritic.evaluate().

    score              — scalar loss + metadata
    quality_assessment — "accept" (< 0.4) | "marginal" [0.4, 0.6) | "reject" (≥ 0.6)
    violations         — top-N dimensions by contribution, sorted desc
    metrics            — raw information-theoretic values for transparency
    top_n              — number of violations returned (default: 3)
    """

    score: AestheticScore
    quality_assessment: Literal["accept", "marginal", "reject"]
    violations: list[Violation]
    metrics: AestheticMetrics
    top_n: int = 3


# ---------------------------------------------------------------------------
# Abstract base class
# ---------------------------------------------------------------------------


class IAestheticCritic(ABC):
    """Stage 2 interface: evaluate source code aesthetic quality.

    Combines information-theoretic metrics (Shannon Entropy, zlib compression
    ratio, Birkhoff Measure) with optional Stage 1 structural metrics
    (L_drift, L_virtue from ProjectionResult) into a unified aesthetic loss.

    Constructor parameters:
        sigma_drift: float = 1.0
            L_drift normalization factor (σ from training distribution).
        min_compression_bytes: int = 50
            Sources shorter than this receive compression_ratio=None and
            zero compression/Birkhoff penalty (satisfies SC-004).
        reject_threshold: float = 0.6
        marginal_threshold: float = 0.4
    """

    @abstractmethod
    def evaluate(
        self,
        source: str,
        language: str,
        projection: ProjectionResult | None = None,
        top_n: int = 3,
    ) -> Critique:
        """Evaluate source code and return a full structured Critique.

        Always returns a Critique — never raises on empty source or
        unsupported language (graceful degradation per contract inv 7-8).
        """
        ...

    @abstractmethod
    def score(
        self,
        source: str,
        language: str,
        projection: ProjectionResult | None = None,
    ) -> float:
        """Return only the scalar aesthetic loss ∈ [0.0, 1.0].

        Equivalent to evaluate(...).score.value (contract invariant 2).
        """
        ...


# ---------------------------------------------------------------------------
# Public re-exports (populated after AestheticCritic is defined)
# ---------------------------------------------------------------------------
from eigenhelm.critic.aesthetic_critic import AestheticCritic  # noqa: E402

__all__ = [
    "IAestheticCritic",
    "AestheticCritic",
    "AestheticMetrics",
    "AestheticScore",
    "Violation",
    "Critique",
]

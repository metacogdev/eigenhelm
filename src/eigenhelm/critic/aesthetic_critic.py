"""AestheticCritic — Stage 2 concrete implementation of IAestheticCritic."""

from __future__ import annotations

from eigenhelm.attribution.constants import DEFAULT_TOP_N
import zlib
from dataclasses import replace
from typing import TYPE_CHECKING, Literal

import numpy as np

from eigenhelm.critic import (
    AestheticMetrics,
    AestheticScore,
    Critique,
    IAestheticCritic,
    Violation,
)
from eigenhelm.config.defaults import DEFAULT_ACCEPT_THRESHOLD, DEFAULT_REJECT_THRESHOLD
from eigenhelm.critic.birkhoff import birkhoff_measure
from eigenhelm.critic.entropy import normalize_entropy, shannon_entropy
from eigenhelm.critic.exemplars import bind_exemplars
from eigenhelm.critic.ncd import ncd_to_nearest_binding

if TYPE_CHECKING:
    from eigenhelm.critic.exemplars import ExemplarBinding
    from eigenhelm.models import ProjectionResult


class AestheticCritic(IAestheticCritic):
    """Concrete information-theoretic aesthetic evaluator.

    Args:
        sigma_drift:           L_drift normalization factor (σ). Default 1.0.
        sigma_virtue:          L_virtue normalization factor. Default 1.0.
        min_compression_bytes: Minimum bytes for compression metrics (SC-004). Default 50.
        reject_threshold:      Loss ≥ this → "reject". Default DEFAULT_REJECT_THRESHOLD.
        marginal_threshold:    Loss ≥ this → "marginal" (else "accept"). Default DEFAULT_ACCEPT_THRESHOLD.
        exemplars:             Decompressed exemplar byte strings for NCD. Default None.
        exemplar_ids:          Content hashes aligned 1:1 with exemplars. When provided,
                               the nearest exemplar identity is reported on Critique for
                               NCD attribution. Must have the same length as exemplars
                               or a ValueError is raised at construction time (62).

    Concurrency:
        Once constructed, AestheticCritic state is immutable: the exemplar
        collection is bound into a tuple of frozen records and stored in a
        single attribute. ``evaluate()`` and ``score()`` may be called from
        many threads concurrently as long as no caller reaches into private
        attributes. See ``docs/concurrency.md`` for the full contract.
    """

    def __init__(
        self,
        sigma_drift: float = 1.0,
        sigma_virtue: float = 1.0,
        min_compression_bytes: int = 50,
        reject_threshold: float = DEFAULT_REJECT_THRESHOLD,
        marginal_threshold: float = DEFAULT_ACCEPT_THRESHOLD,
        exemplars: list[bytes] | None = None,
        exemplar_ids: list[str] | None = None,
    ) -> None:
        if sigma_drift <= 0:
            raise ValueError(f"sigma_drift must be > 0, got {sigma_drift}")
        if sigma_virtue <= 0:
            raise ValueError(f"sigma_virtue must be > 0, got {sigma_virtue}")
        self.sigma_drift = sigma_drift
        self.sigma_virtue = sigma_virtue
        self.min_compression_bytes = min_compression_bytes
        self.reject_threshold = reject_threshold
        self.marginal_threshold = marginal_threshold
        # 62: bind (bytes, identity) into a single immutable tuple so a single
        # attribute read returns a self-consistent snapshot under concurrent use.
        # bind_exemplars validates length alignment and raises ValueError early.
        self._exemplars: tuple[ExemplarBinding, ...] | None = bind_exemplars(
            exemplars, exemplar_ids
        )

    # ------------------------------------------------------------------
    # US1: Information-theoretic metrics
    # ------------------------------------------------------------------

    def _compute_metrics(self, source: str, language: str) -> AestheticMetrics:  # noqa: ARG002
        """Compute raw AestheticMetrics from source.

        `language` is accepted for API consistency but does not affect computation.
        zlib.compress() is always called to populate compressed_bytes (data-model invariant).
        compression_ratio and birkhoff_measure are gated by min_compression_bytes.
        """
        src_bytes = source.encode("utf-8")
        raw_bytes = len(src_bytes)
        compressed_bytes = len(zlib.compress(src_bytes, level=6))

        h = shannon_entropy(source)

        if raw_bytes < self.min_compression_bytes:
            comp_ratio = None
            bm = 0.0
        else:
            comp_ratio = compressed_bytes / raw_bytes
            bm = birkhoff_measure(h, raw_bytes, compressed_bytes)

        return AestheticMetrics(
            entropy=h,
            compression_ratio=comp_ratio,
            birkhoff_measure=bm,
            raw_bytes=raw_bytes,
            compressed_bytes=compressed_bytes,
        )

    # ------------------------------------------------------------------
    # US2: Unified aesthetic score
    # ------------------------------------------------------------------

    def _normalize_dimensions(
        self,
        metrics: AestheticMetrics,
        projection: ProjectionResult | None,
    ) -> dict[str, float]:
        """Normalize each dimension to [0, 1] penalty contribution.

        Returns a dict keyed by the canonical dimension names defined in Violation.
        Structural dimensions are 0.0 when projection is None.
        """
        norm: dict[str, float] = {}

        if projection is not None:
            norm["manifold_drift"] = min(projection.l_drift / self.sigma_drift, 1.0)
            norm["manifold_alignment"] = min(
                projection.l_virtue / self.sigma_virtue, 1.0
            )
        else:
            norm["manifold_drift"] = 0.0
            norm["manifold_alignment"] = 0.0

        norm["token_entropy"] = normalize_entropy(metrics.entropy)
        norm["compression_structure"] = metrics.birkhoff_measure

        return norm

    def _select_weights(self, projection: ProjectionResult | None) -> dict[str, float]:
        """Return per-dimension weights summing to 1.0.

        Four configurations based on projection and exemplar availability.
        Structural dimensions (drift, alignment) weighted higher than surface
        metrics (entropy, compression) when projection is available (013).
        """
        from eigenhelm.config.defaults import WEIGHT_PROFILES
        
        if projection is not None and self._exemplars is not None:
            return WEIGHT_PROFILES["projection_and_exemplars"]
        if projection is not None:
            return WEIGHT_PROFILES["projection_only"]
        if self._exemplars is not None:
            return WEIGHT_PROFILES["exemplars_only"]
        return WEIGHT_PROFILES["fallback"]

    def _compute_score(
        self,
        normalized: dict[str, float],
        weights: dict[str, float],
        projection: ProjectionResult | None,
    ) -> AestheticScore:
        """Compute the weighted aesthetic loss and return AestheticScore."""
        contributions = {dim: normalized[dim] * weights[dim] for dim in weights}
        value = sum(contributions.values())
        value = max(0.0, min(1.0, value))  # clamp by construction (weights sum to 1)
        confidence = "high" if projection is not None else "low"
        return AestheticScore(
            value=value,
            structural_confidence=confidence,
            weights=dict(weights),
            contributions=contributions,
            normalized_values=dict(normalized),
        )

    # ------------------------------------------------------------------
    # US3: Ranked violations + full Critique
    # ------------------------------------------------------------------

    def _rank_violations(
        self,
        normalized: dict[str, float],
        raw_values: dict[str, float],
        weights: dict[str, float],
        total_loss: float,
        top_n: int,
    ) -> list[Violation]:
        """Rank dimensions by contribution and return top-N Violation objects.

        Returns [] when total_loss == 0.0 (all dimensions at ideal).
        Skips dimensions with zero weight.

        Args:
            normalized:  Pre-normalized [0,1] values per dimension.
            raw_values:  Original (un-normalized) metric values per dimension.
                         E.g., entropy in bits/byte for token_entropy,
                         l_drift for manifold_drift.
            weights:     Per-dimension weights.
            total_loss:  Weighted sum (AestheticScore.value).
            top_n:       Maximum violations to return.
        """
        if total_loss == 0.0:
            return []

        violations: list[Violation] = []
        for dim, norm_val in normalized.items():
            w = weights.get(dim, 0.0)
            if w == 0.0:
                continue
            contribution = (norm_val * w) / total_loss
            violations.append(
                Violation(
                    dimension=dim,  # type: ignore[arg-type]
                    raw_value=raw_values[dim],
                    normalized_value=norm_val,
                    contribution=contribution,
                    weighted_contribution=norm_val * w,
                )
            )

        violations.sort(key=lambda v: v.contribution, reverse=True)
        return violations[:top_n]

    def _empty_critique(self, top_n: int) -> Critique:
        """Build the invariant-preserving critique for empty source."""
        empty_metrics = AestheticMetrics(
            entropy=0.0,
            compression_ratio=None,
            birkhoff_measure=0.0,
            raw_bytes=0,
            compressed_bytes=len(zlib.compress(b"", level=6)),
        )
        empty_score = AestheticScore(
            value=0.0,
            structural_confidence="low",
            weights=self._select_weights(None),
        )
        return Critique(
            score=empty_score,
            quality_assessment="accept",
            violations=[],
            metrics=empty_metrics,
            top_n=top_n,
        )

    def _add_ncd_distance(
        self,
        source: str,
        normalized: dict[str, float],
    ) -> str | None:
        """Populate normalized NCD distance and return the nearest exemplar id."""
        exemplars = self._exemplars
        if exemplars is None:
            normalized["ncd_exemplar_distance"] = 0.0
            return None

        ncd_result = ncd_to_nearest_binding(
            source.encode("utf-8"),
            exemplars,
            min_bytes=self.min_compression_bytes,
        )
        if ncd_result is None:
            normalized["ncd_exemplar_distance"] = 0.0
            return None

        ncd_dist, nearest_id = ncd_result
        normalized["ncd_exemplar_distance"] = ncd_dist
        return nearest_id

    def _dampen_declaration_dimensions(
        self,
        normalized: dict[str, float],
        declaration_dominant: bool,
    ) -> None:
        """Dampen projection dimensions for declaration-dominant files."""
        if not declaration_dominant:
            return

        normalized["manifold_drift"] *= 0.5
        normalized["manifold_alignment"] *= 0.5

    def _clamp_declaration_score(
        self,
        score: AestheticScore,
        declaration_dominant: bool,
    ) -> AestheticScore:
        """Apply the declaration-dominant marginal-threshold score floor."""
        if declaration_dominant and score.value < self.marginal_threshold:
            return replace(score, value=self.marginal_threshold)
        return score

    def _raw_values(
        self,
        metrics: AestheticMetrics,
        normalized: dict[str, float],
        projection: ProjectionResult | None,
    ) -> dict[str, float]:
        """Return raw metric values aligned with normalized dimensions."""
        return {
            "manifold_drift": projection.l_drift if projection is not None else 0.0,
            "manifold_alignment": projection.l_virtue
            if projection is not None
            else 0.0,
            "token_entropy": metrics.entropy,
            "compression_structure": metrics.birkhoff_measure,
            "ncd_exemplar_distance": normalized["ncd_exemplar_distance"],
        }

    def _quality_assessment(
        self, score: AestheticScore
    ) -> Literal["accept", "marginal", "reject"]:
        """Map a scalar loss to the public quality assessment label."""
        if score.value >= self.reject_threshold:
            return "reject"
        if score.value >= self.marginal_threshold:
            return "marginal"
        return "accept"

    def _detect_anti_patterns(self, feature_vector: np.ndarray | None) -> list:
        """Run anti-pattern detectors when a feature vector is available."""
        if feature_vector is None:
            return []

        from eigenhelm.critic.anti_patterns import detect_anti_patterns

        return detect_anti_patterns(feature_vector)

    def evaluate(
        self,
        source: str,
        language: str,
        projection: ProjectionResult | None = None,
        top_n: int = DEFAULT_TOP_N,
        feature_vector: np.ndarray | None = None,
        declaration_dominant: bool = False,
    ) -> Critique:
        """Evaluate source code and return a full structured Critique.

        Never raises on empty source or unsupported language (invariants 7-8).
        Empty source → loss=0.0, quality="accept", violations=[].
        feature_vector: optional FeatureVector.values for anti-pattern detection.
        """
        if not source:
            return self._empty_critique(top_n)

        metrics = self._compute_metrics(source, language)
        normalized = self._normalize_dimensions(metrics, projection)

        # Compute NCD exemplar distance (010) and inject into normalized dict.
        # 62: single atomic read of the bound exemplar tuple — reading bytes
        # and identity through one immutable record prevents the two from
        # desynchronizing if exemplar state is swapped on another thread.
        nearest_exemplar_id = self._add_ncd_distance(source, normalized)

        # 020: Dampen drift and alignment for declaration-dominant files
        self._dampen_declaration_dimensions(normalized, declaration_dominant)

        weights = self._select_weights(projection)
        score = self._compute_score(normalized, weights, projection)

        # 020: Clamp to accept threshold floor for declaration-dominant files
        score = self._clamp_declaration_score(score, declaration_dominant)

        raw_values = self._raw_values(metrics, normalized, projection)
        violations = self._rank_violations(
            normalized, raw_values, weights, score.value, top_n
        )

        # Run anti-pattern detectors (011) when feature vector is available
        anti_pattern_violations = self._detect_anti_patterns(feature_vector)

        return Critique(
            score=score,
            quality_assessment=self._quality_assessment(score),
            violations=violations,
            metrics=metrics,
            top_n=top_n,
            anti_patterns=anti_pattern_violations,
            nearest_exemplar_id=nearest_exemplar_id,
        )

    def score(
        self,
        source: str,
        language: str,
        projection: ProjectionResult | None = None,
    ) -> float:
        """Return only the scalar aesthetic loss ∈ [0.0, 1.0].

        Equivalent to evaluate(...).score.value (invariant 2).
        """
        return self.evaluate(source, language, projection).score.value

"""AestheticCritic — Stage 2 concrete implementation of IAestheticCritic."""

from __future__ import annotations

import zlib
from typing import TYPE_CHECKING

import numpy as np

from eigenhelm.critic import AestheticMetrics, AestheticScore, Critique, IAestheticCritic, Violation
from eigenhelm.critic.birkhoff import birkhoff_measure
from eigenhelm.critic.entropy import shannon_entropy
from eigenhelm.critic.ncd import ncd_to_exemplars, ncd_to_exemplars_with_id

if TYPE_CHECKING:
    from eigenhelm.models import ProjectionResult


class AestheticCritic(IAestheticCritic):
    """Concrete information-theoretic aesthetic evaluator.

    Args:
        sigma_drift:           L_drift normalization factor (σ). Default 1.0.
        sigma_virtue:          L_virtue normalization factor. Default 1.0.
        min_compression_bytes: Minimum bytes for compression metrics (SC-004). Default 50.
        reject_threshold:      Loss ≥ this → "reject". Default 0.6.
        marginal_threshold:    Loss ≥ this → "marginal" (else "accept"). Default 0.4.
        exemplars:             Decompressed exemplar byte strings for NCD. Default None.
        exemplar_ids:          Content hashes aligned 1:1 with exemplars. When provided,
                               the nearest exemplar identity is reported on Critique for
                               NCD attribution. Must have the same length as exemplars.
    """

    def __init__(
        self,
        sigma_drift: float = 1.0,
        sigma_virtue: float = 1.0,
        min_compression_bytes: int = 50,
        reject_threshold: float = 0.6,
        marginal_threshold: float = 0.4,
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
        self._exemplars = exemplars
        self._exemplar_ids = exemplar_ids

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
            norm["manifold_alignment"] = min(projection.l_virtue / self.sigma_virtue, 1.0)
        else:
            norm["manifold_drift"] = 0.0
            norm["manifold_alignment"] = 0.0

        norm["token_entropy"] = 1.0 - (metrics.entropy / 8.0)
        norm["compression_structure"] = metrics.birkhoff_measure

        return norm

    def _select_weights(self, projection: ProjectionResult | None) -> dict[str, float]:
        """Return per-dimension weights summing to 1.0.

        Four configurations based on projection and exemplar availability.
        Structural dimensions (drift, alignment) weighted higher than surface
        metrics (entropy, compression) when projection is available (013).
        """
        if projection is not None and self._exemplars is not None:
            return {
                "manifold_drift": 0.30,
                "manifold_alignment": 0.30,
                "token_entropy": 0.15,
                "compression_structure": 0.15,
                "ncd_exemplar_distance": 0.10,
            }
        if projection is not None:
            return {
                "manifold_drift": 0.35,
                "manifold_alignment": 0.35,
                "token_entropy": 0.15,
                "compression_structure": 0.15,
                "ncd_exemplar_distance": 0.0,
            }
        if self._exemplars is not None:
            return {
                "manifold_drift": 0.0,
                "manifold_alignment": 0.0,
                "token_entropy": 0.30,
                "compression_structure": 0.30,
                "ncd_exemplar_distance": 0.40,
            }
        return {
            "manifold_drift": 0.0,
            "manifold_alignment": 0.0,
            "token_entropy": 0.5,
            "compression_structure": 0.5,
            "ncd_exemplar_distance": 0.0,
        }

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

    def evaluate(
        self,
        source: str,
        language: str,
        projection: ProjectionResult | None = None,
        top_n: int = 3,
        feature_vector: np.ndarray | None = None,
    ) -> Critique:
        """Evaluate source code and return a full structured Critique.

        Never raises on empty source or unsupported language (invariants 7-8).
        Empty source → loss=0.0, quality="accept", violations=[].
        feature_vector: optional FeatureVector.values for anti-pattern detection.
        """
        if not source:
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

        metrics = self._compute_metrics(source, language)
        normalized = self._normalize_dimensions(metrics, projection)

        # Compute NCD exemplar distance (010) and inject into normalized dict
        nearest_exemplar_id: str | None = None
        if self._exemplars is not None:
            source_bytes = source.encode("utf-8")
            if self._exemplar_ids is not None:
                ncd_result = ncd_to_exemplars_with_id(
                    source_bytes, self._exemplars, self._exemplar_ids,
                    min_bytes=self.min_compression_bytes,
                )
                if ncd_result is not None:
                    ncd_dist, nearest_exemplar_id = ncd_result
                else:
                    ncd_dist = None
            else:
                ncd_dist = ncd_to_exemplars(
                    source_bytes, self._exemplars, min_bytes=self.min_compression_bytes
                )
            normalized["ncd_exemplar_distance"] = ncd_dist if ncd_dist is not None else 0.0
        else:
            normalized["ncd_exemplar_distance"] = 0.0

        weights = self._select_weights(projection)
        score = self._compute_score(normalized, weights, projection)

        raw_values: dict[str, float] = {
            "manifold_drift": projection.l_drift if projection is not None else 0.0,
            "manifold_alignment": projection.l_virtue if projection is not None else 0.0,
            "token_entropy": metrics.entropy,
            "compression_structure": metrics.birkhoff_measure,
            "ncd_exemplar_distance": normalized["ncd_exemplar_distance"],
        }
        violations = self._rank_violations(normalized, raw_values, weights, score.value, top_n)

        if score.value >= self.reject_threshold:
            quality = "reject"
        elif score.value >= self.marginal_threshold:
            quality = "marginal"
        else:
            quality = "accept"

        # Run anti-pattern detectors (011) when feature vector is available
        anti_pattern_violations: list = []
        if feature_vector is not None:
            from eigenhelm.critic.anti_patterns import detect_anti_patterns

            anti_pattern_violations = detect_anti_patterns(feature_vector)

        return Critique(
            score=score,
            quality_assessment=quality,
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

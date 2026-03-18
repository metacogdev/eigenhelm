"""Constants for score attribution and directive generation."""

from __future__ import annotations

# Canonical names for all 69 features in the feature vector.
# [0-4]: scalar metrics, [5-68]: WL hash histogram bins.
FEATURE_NAMES: tuple[str, ...] = (
    "halstead_volume",
    "halstead_difficulty",
    "halstead_effort",
    "cyclomatic_complexity",
    "cyclomatic_density",
    *(f"wl_hash_bin_{i:02d}" for i in range(64)),
)

# Fixed directive vocabulary — closed set of category labels.
DIRECTIVE_VOCABULARY: frozenset[str] = frozenset({
    "reduce_complexity",
    "review_token_distribution",
    "extract_repeated_logic",
    "review_structure",
    "improve_compression",
})

# Canonical dimension names in stable order.
DIMENSION_NAMES: tuple[str, ...] = (
    "manifold_drift",
    "manifold_alignment",
    "token_entropy",
    "compression_structure",
    "ncd_exemplar_distance",
)

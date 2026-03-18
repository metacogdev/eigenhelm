"""Directive generation from attribution data.

Maps dimension attributions to structured directive records using
a fixed vocabulary of category labels.
"""

from __future__ import annotations

from eigenhelm.attribution.models import DimensionAttribution, Directive

# Feature-to-category mapping for PCA dimensions.
# Features [0-4] (scalar metrics) → "reduce_complexity"
# Features [5-68] (WL hash bins) → depends on deviation direction
_SCALAR_FEATURE_INDICES = frozenset(range(5))

# Direct dimension-to-category mapping for information-theoretic dimensions
_DIRECT_CATEGORY: dict[str, str] = {
    "token_entropy": "review_token_distribution",
    "compression_structure": "improve_compression",
    "ncd_exemplar_distance": "review_structure",
}


def _derive_severity(normalized_score: float) -> str:
    """Derive severity from the dimension's normalized score."""
    if normalized_score >= 0.7:
        return "high"
    if normalized_score >= 0.5:
        return "medium"
    return "low"


def _category_for_pca_dim(dim: DimensionAttribution) -> str:
    """Determine directive category from the top-contributing feature."""
    if not dim.features:
        return "review_structure"

    top = dim.features[0]

    if top.feature_index in _SCALAR_FEATURE_INDICES:
        return "reduce_complexity"

    # WL hash bin — direction from standardized_deviation
    if top.standardized_deviation > 0:
        return "extract_repeated_logic"
    return "review_structure"


def _category_for_direct_dim(dim: DimensionAttribution) -> str:
    """Determine directive category for a direct (info-theoretic) dimension."""
    return _DIRECT_CATEGORY.get(dim.dimension, "review_structure")


# Dimensions where high severity is misleading on small files because
# the metric is dominated by file size rather than code quality.
_SIZE_SENSITIVE_DIMENSIONS = frozenset({"compression_structure", "ncd_exemplar_distance"})

# Files at or below this line count get severity-capped for size-sensitive dims.
_SMALL_FILE_LINE_THRESHOLD = 80

# Maximum severity for size-sensitive dimensions in small files.
_SMALL_FILE_SEVERITY_CAP = "medium"


def generate_directives(
    dimensions: tuple[DimensionAttribution, ...],
    threshold: float = 0.3,
    source_line_count: int | None = None,
) -> tuple[Directive, ...]:
    """Generate directive records from dimension attributions.

    A directive is produced for each dimension where:
    - available is True
    - normalized_score > threshold

    Args:
        dimensions: All dimension attributions from compute_attribution().
        threshold: Minimum normalized_score to produce a directive.
        source_line_count: Total lines in the evaluated source. When provided
            and the file is small (≤80 lines), size-sensitive dimensions
            (compression_structure, ncd_exemplar_distance) have their
            severity capped at "medium" to avoid misleading agents into
            futile refactoring loops.

    Returns:
        Tuple of Directive records (may be empty).
    """
    is_small_file = (
        source_line_count is not None
        and source_line_count <= _SMALL_FILE_LINE_THRESHOLD
    )

    directives: list[Directive] = []

    for dim in dimensions:
        if not dim.available or dim.normalized_score <= threshold:
            continue
        if dim.source_location is None:
            continue

        if dim.features:
            category = _category_for_pca_dim(dim)
        else:
            category = _category_for_direct_dim(dim)

        severity = _derive_severity(dim.normalized_score)

        if is_small_file and dim.dimension in _SIZE_SENSITIVE_DIMENSIONS:
            if severity == "high":
                severity = _SMALL_FILE_SEVERITY_CAP

        directives.append(
            Directive(
                category=category,
                dimension=dim.dimension,
                normalized_score=dim.normalized_score,
                attribution=dim,
                source_location=dim.source_location,
                severity=severity,
            )
        )

    return tuple(directives)

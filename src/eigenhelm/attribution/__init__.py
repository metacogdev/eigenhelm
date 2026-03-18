"""Score attribution and directive generation.

Decomposes eigenhelm's 5-dimension scoring into per-feature contributions,
maps those to source code locations, and produces structured directive records.

Public API:
    compute_attribution() — orchestrate full attribution chain
"""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from eigenhelm.attribution.decompose import (
    attribute_direct,
    decompose_alignment,
    decompose_drift,
)
from eigenhelm.attribution.directives import generate_directives
from eigenhelm.attribution.models import AttributionResult, DimensionAttribution
from eigenhelm.attribution.source_map import (
    source_location_from_code_unit,
    source_location_from_source,
)

if TYPE_CHECKING:
    from eigenhelm.attribution.models import SourceLocation
    from eigenhelm.critic import AestheticMetrics
    from eigenhelm.models import EigenspaceModel, FeatureVector, ProjectionResult


def _attach_source_location(
    dim: DimensionAttribution, location: SourceLocation | None
) -> DimensionAttribution:
    """Attach source location to a dimension attribution.

    If the dimension is available but no location can be provided,
    marks the dimension as unavailable per contract invariant.
    """
    if not dim.available:
        return dim
    if location is None:
        # Contract: available dims must have source_location
        return replace(dim, available=False, source_location=None)
    return replace(dim, source_location=location)


def compute_attribution(
    metrics: AestheticMetrics,
    normalized_values: dict[str, float],
    projection: ProjectionResult | None = None,
    model: EigenspaceModel | None = None,
    feature_vector: FeatureVector | None = None,
    nearest_exemplar_id: str | None = None,
    source: str | None = None,
    file_path: str | None = None,
    top_n: int = 3,
    directive_threshold: float = 0.3,
) -> AttributionResult:
    """Compute full attribution for an evaluation result.

    Orchestrates decompose_drift, decompose_alignment, and attribute_direct
    for all 5 dimensions. Attaches source locations from CodeUnit or source.
    """
    # Determine source locations
    structural_loc = None
    if feature_vector is not None:
        structural_loc = source_location_from_code_unit(feature_vector.code_unit)

    source_loc = None
    if source is not None:
        source_loc = source_location_from_source(source, file_path)

    dimensions: list[DimensionAttribution] = []

    # Structural dimensions (PCA-based)
    if projection is not None and model is not None and feature_vector is not None:
        drift = decompose_drift(projection, model, feature_vector, top_n)
        align = decompose_alignment(projection, model, feature_vector, top_n)
        dimensions.append(_attach_source_location(drift, structural_loc))
        dimensions.append(_attach_source_location(align, structural_loc))
    else:
        drift_score = 0.0
        align_score = 0.0
        if projection is not None and model is not None:
            drift_score = min(max(projection.l_drift / model.sigma_drift, 0.0), 1.0)
            align_score = min(max(projection.l_virtue / model.sigma_virtue, 0.0), 1.0)
        dimensions.append(
            DimensionAttribution(
                dimension="manifold_drift",
                normalized_score=drift_score,
                available=False,
                method="pca_reconstruction",
            )
        )
        dimensions.append(
            DimensionAttribution(
                dimension="manifold_alignment",
                normalized_score=align_score,
                available=False,
                method="pca_alignment",
            )
        )

    # Information-theoretic dimensions (direct) — use full source location
    entropy = attribute_direct("token_entropy", metrics, normalized_values)
    dimensions.append(_attach_source_location(entropy, source_loc))

    compression = attribute_direct("compression_structure", metrics, normalized_values)
    dimensions.append(_attach_source_location(compression, source_loc))

    ncd = attribute_direct(
        "ncd_exemplar_distance",
        metrics,
        normalized_values,
        nearest_exemplar_id=nearest_exemplar_id,
    )
    dimensions.append(_attach_source_location(ncd, source_loc))

    dims_tuple = tuple(dimensions)
    source_line_count = source.count("\n") + 1 if source else None
    directives = generate_directives(
        dims_tuple,
        threshold=directive_threshold,
        source_line_count=source_line_count,
    )

    return AttributionResult(
        dimensions=dims_tuple,
        directives=directives,
        top_n=top_n,
        directive_threshold=directive_threshold,
    )

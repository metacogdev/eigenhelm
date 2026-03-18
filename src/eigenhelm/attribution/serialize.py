"""Serialization helpers for attribution dataclasses to dicts.

Used by JSON, SARIF, and HTTP output formatters.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from eigenhelm.attribution.models import AttributionResult


def attribution_to_dict(attr: AttributionResult | None) -> dict | None:
    """Serialize an AttributionResult to a JSON-compatible dict."""
    if attr is None:
        return None

    return {
        "dimensions": [_dimension_to_dict(d) for d in attr.dimensions],
        "directives": [_directive_to_dict(d) for d in attr.directives],
        "top_n": attr.top_n,
        "directive_threshold": attr.directive_threshold,
        "vocabulary_version": attr.vocabulary_version,
    }


def _source_location_to_dict(loc) -> dict | None:
    if loc is None:
        return None
    return {
        "code_unit_name": loc.code_unit_name,
        "start_line": loc.start_line,
        "end_line": loc.end_line,
        "file_path": loc.file_path,
    }


def _feature_to_dict(f) -> dict:
    return {
        "feature_index": f.feature_index,
        "feature_name": f.feature_name,
        "contribution_value": f.contribution_value,
        "contribution_magnitude": f.contribution_magnitude,
        "raw_value": f.raw_value,
        "corpus_mean": f.corpus_mean,
        "standardized_deviation": f.standardized_deviation,
        "rank": f.rank,
    }


def _direct_attribution_to_dict(d) -> dict | None:
    if d is None:
        return None
    return {
        "metric_name": d.metric_name,
        "computed_value": d.computed_value,
        "normalization": d.normalization,
        "normalized_score": d.normalized_score,
        "exemplar_id": d.exemplar_id,
    }


def _dimension_to_dict(d) -> dict:
    return {
        "dimension": d.dimension,
        "normalized_score": d.normalized_score,
        "available": d.available,
        "method": d.method,
        "source_location": _source_location_to_dict(d.source_location),
        "features": [_feature_to_dict(f) for f in d.features],
        "direct": _direct_attribution_to_dict(d.direct),
    }


def _directive_to_dict(d) -> dict:
    return {
        "category": d.category,
        "dimension": d.dimension,
        "normalized_score": d.normalized_score,
        "attribution": _dimension_to_dict(d.attribution),
        "source_location": _source_location_to_dict(d.source_location),
        "severity": d.severity,
    }

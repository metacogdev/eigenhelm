"""Tests for directive generation from attribution data (017-score-attribution).

Covers:
  T021 — Directive generation rules, severity derivation, category mapping.
"""

from __future__ import annotations

import pytest

from eigenhelm.attribution.directives import generate_directives
from eigenhelm.attribution.models import (
    DimensionAttribution,
    DirectAttribution,
    Directive,
    FeatureContribution,
    SourceLocation,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_LOC = SourceLocation(
    code_unit_name="func", start_line=1, end_line=10, file_path="f.py"
)


def _pca_dim(
    dimension: str = "manifold_drift",
    score: float = 0.6,
    available: bool = True,
    feature_index: int = 0,
    feature_name: str = "halstead_volume",
    std_dev: float = 1.5,
) -> DimensionAttribution:
    """Build a PCA-based DimensionAttribution with one top feature."""
    feat = FeatureContribution(
        feature_index=feature_index,
        feature_name=feature_name,
        contribution_value=0.8,
        contribution_magnitude=0.8,
        raw_value=5.0,
        corpus_mean=3.0,
        standardized_deviation=std_dev,
        rank=1,
    )
    return DimensionAttribution(
        dimension=dimension,
        normalized_score=score,
        available=available,
        method="pca",
        source_location=_LOC,
        features=(feat,),
    )


def _direct_dim(
    dimension: str = "token_entropy",
    score: float = 0.6,
    available: bool = True,
    metric_name: str = "token_entropy",
) -> DimensionAttribution:
    """Build a direct DimensionAttribution."""
    return DimensionAttribution(
        dimension=dimension,
        normalized_score=score,
        available=available,
        method="direct",
        source_location=_LOC,
        direct=DirectAttribution(
            metric_name=metric_name,
            computed_value=0.5,
            normalization="linear",
            normalized_score=score,
        ),
    )


# ---------------------------------------------------------------------------
# (a) Dimension above threshold generates directive with correct category
# ---------------------------------------------------------------------------


def test_above_threshold_generates_directive() -> None:
    dims = (_pca_dim(score=0.5),)
    result = generate_directives(dims, threshold=0.3)
    assert len(result) == 1
    assert isinstance(result[0], Directive)
    assert result[0].category == "reduce_complexity"


# ---------------------------------------------------------------------------
# (b) Dimension below threshold generates no directive
# ---------------------------------------------------------------------------


def test_below_threshold_no_directive() -> None:
    dims = (_pca_dim(score=0.2),)
    result = generate_directives(dims, threshold=0.3)
    assert result == ()


# ---------------------------------------------------------------------------
# (c) All dimensions below threshold → empty tuple
# ---------------------------------------------------------------------------


def test_all_below_threshold_empty() -> None:
    dims = (
        _pca_dim(score=0.1),
        _direct_dim(score=0.05),
    )
    result = generate_directives(dims, threshold=0.3)
    assert result == ()


# ---------------------------------------------------------------------------
# (d) Severity derivation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "score, expected_severity",
    [
        (0.35, "low"),
        (0.49, "low"),
        (0.5, "medium"),
        (0.69, "medium"),
        (0.7, "high"),
        (0.95, "high"),
    ],
)
def test_severity_derivation(score: float, expected_severity: str) -> None:
    dims = (_pca_dim(score=score),)
    result = generate_directives(dims, threshold=0.3)
    assert len(result) == 1
    assert result[0].severity == expected_severity


# ---------------------------------------------------------------------------
# (e) PCA dim with halstead top contributor → "reduce_complexity"
# ---------------------------------------------------------------------------


def test_pca_halstead_reduce_complexity() -> None:
    dims = (_pca_dim(feature_index=2, feature_name="halstead_effort"),)
    result = generate_directives(dims, threshold=0.3)
    assert result[0].category == "reduce_complexity"


# ---------------------------------------------------------------------------
# (f) PCA dim with wl_hash positive std_dev → "extract_repeated_logic"
# ---------------------------------------------------------------------------


def test_pca_wl_hash_positive_extract_repeated() -> None:
    dims = (_pca_dim(feature_index=10, feature_name="wl_hash_bin_05", std_dev=2.0),)
    result = generate_directives(dims, threshold=0.3)
    assert result[0].category == "extract_repeated_logic"


# ---------------------------------------------------------------------------
# (g) PCA dim with wl_hash negative std_dev → "review_structure"
# ---------------------------------------------------------------------------


def test_pca_wl_hash_negative_review_structure() -> None:
    dims = (_pca_dim(feature_index=10, feature_name="wl_hash_bin_05", std_dev=-1.0),)
    result = generate_directives(dims, threshold=0.3)
    assert result[0].category == "review_structure"


# ---------------------------------------------------------------------------
# (h) token_entropy direct dim → "review_token_distribution"
# ---------------------------------------------------------------------------


def test_direct_token_entropy() -> None:
    dims = (_direct_dim(dimension="token_entropy", metric_name="token_entropy"),)
    result = generate_directives(dims, threshold=0.3)
    assert result[0].category == "review_token_distribution"


# ---------------------------------------------------------------------------
# (i) compression_structure direct dim → "improve_compression"
# ---------------------------------------------------------------------------


def test_direct_compression_structure() -> None:
    dims = (
        _direct_dim(
            dimension="compression_structure", metric_name="compression_structure"
        ),
    )
    result = generate_directives(dims, threshold=0.3)
    assert result[0].category == "improve_compression"


# ---------------------------------------------------------------------------
# (j) ncd_exemplar_distance direct dim → "review_structure"
# ---------------------------------------------------------------------------


def test_direct_ncd_exemplar_distance() -> None:
    dims = (
        _direct_dim(
            dimension="ncd_exemplar_distance", metric_name="ncd_exemplar_distance"
        ),
    )
    result = generate_directives(dims, threshold=0.3)
    assert result[0].category == "review_structure"


# ---------------------------------------------------------------------------
# (k) Configurable threshold respected
# ---------------------------------------------------------------------------


def test_configurable_threshold() -> None:
    dim = _pca_dim(score=0.45)
    # Below custom threshold of 0.5 → no directive
    assert generate_directives((dim,), threshold=0.5) == ()
    # Above custom threshold of 0.4 → directive generated
    result = generate_directives((dim,), threshold=0.4)
    assert len(result) == 1


# ---------------------------------------------------------------------------
# (l) Small-file severity cap for size-sensitive dimensions
# ---------------------------------------------------------------------------


def test_small_file_caps_compression_severity() -> None:
    """compression_structure with high score on a small file → capped to medium."""
    dims = (
        _direct_dim(
            dimension="compression_structure",
            metric_name="compression_structure",
            score=0.92,
        ),
    )
    result = generate_directives(dims, threshold=0.3, source_line_count=50)
    assert len(result) == 1
    assert result[0].severity == "medium"


def test_small_file_caps_ncd_severity() -> None:
    """ncd_exemplar_distance with high score on a small file → capped to medium."""
    dims = (
        _direct_dim(
            dimension="ncd_exemplar_distance",
            metric_name="ncd_exemplar_distance",
            score=0.85,
        ),
    )
    result = generate_directives(dims, threshold=0.3, source_line_count=40)
    assert len(result) == 1
    assert result[0].severity == "medium"


def test_large_file_no_severity_cap() -> None:
    """compression_structure on a large file retains high severity."""
    dims = (
        _direct_dim(
            dimension="compression_structure",
            metric_name="compression_structure",
            score=0.92,
        ),
    )
    result = generate_directives(dims, threshold=0.3, source_line_count=200)
    assert len(result) == 1
    assert result[0].severity == "high"


def test_small_file_no_cap_when_already_medium() -> None:
    """Medium severity on a small file stays medium (no downgrade to low)."""
    dims = (
        _direct_dim(
            dimension="compression_structure",
            metric_name="compression_structure",
            score=0.55,
        ),
    )
    result = generate_directives(dims, threshold=0.3, source_line_count=30)
    assert len(result) == 1
    assert result[0].severity == "medium"


def test_small_file_pca_dims_not_capped() -> None:
    """PCA-based dimensions are NOT size-sensitive — no cap applied."""
    dims = (_pca_dim(score=0.8),)
    result = generate_directives(dims, threshold=0.3, source_line_count=30)
    assert len(result) == 1
    assert result[0].severity == "high"


def test_no_line_count_no_cap() -> None:
    """When source_line_count is None, no cap is applied (backward compat)."""
    dims = (
        _direct_dim(
            dimension="compression_structure",
            metric_name="compression_structure",
            score=0.92,
        ),
    )
    result = generate_directives(dims, threshold=0.3)
    assert len(result) == 1
    assert result[0].severity == "high"

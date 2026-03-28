"""Unit tests for declaration-aware directive category override."""

from __future__ import annotations

from eigenhelm.attribution.directives import generate_directives
from eigenhelm.attribution.models import (
    DimensionAttribution,
    FeatureContribution,
    SourceLocation,
)


def _make_wl_hash_dim(stddev: float = 1.0) -> DimensionAttribution:
    """Create a PCA dimension attribution with a WL-hash top feature."""
    return DimensionAttribution(
        dimension="manifold_drift",
        normalized_score=0.8,
        available=True,
        method="pca_reconstruction",
        source_location=SourceLocation(
            code_unit_name="Foo",
            start_line=1,
            end_line=10,
        ),
        features=(
            FeatureContribution(
                feature_index=10,  # WL hash bin (>= 5)
                feature_name="wl_hash_10",
                contribution_value=0.5,
                contribution_magnitude=0.5,
                raw_value=3.0,
                corpus_mean=1.0,
                standardized_deviation=stddev,
                rank=0,
            ),
        ),
    )


def test_declaration_dominant_overrides_extract_repeated_logic():
    dim = _make_wl_hash_dim(stddev=1.0)  # positive deviation → extract_repeated_logic
    directives = generate_directives((dim,), declaration_dominant=True)
    assert len(directives) == 1
    assert directives[0].category == "review_structure"


def test_non_declaration_preserves_extract_repeated_logic():
    dim = _make_wl_hash_dim(stddev=1.0)
    directives = generate_directives((dim,), declaration_dominant=False)
    assert len(directives) == 1
    assert directives[0].category == "extract_repeated_logic"


def test_declaration_dominant_does_not_affect_negative_deviation():
    dim = _make_wl_hash_dim(
        stddev=-1.0
    )  # negative deviation → review_structure already
    directives = generate_directives((dim,), declaration_dominant=True)
    assert len(directives) == 1
    assert directives[0].category == "review_structure"


def test_declaration_dominant_does_not_affect_scalar_features():
    """Scalar metric features (indices 0-4) should not be overridden."""
    dim = DimensionAttribution(
        dimension="manifold_drift",
        normalized_score=0.8,
        available=True,
        method="pca_reconstruction",
        source_location=SourceLocation(code_unit_name="Foo", start_line=1, end_line=10),
        features=(
            FeatureContribution(
                feature_index=2,  # Scalar metric (< 5)
                feature_name="halstead_effort",
                contribution_value=0.5,
                contribution_magnitude=0.5,
                raw_value=3.0,
                corpus_mean=1.0,
                standardized_deviation=1.0,
                rank=0,
            ),
        ),
    )
    directives = generate_directives((dim,), declaration_dominant=True)
    assert len(directives) == 1
    assert directives[0].category == "reduce_complexity"

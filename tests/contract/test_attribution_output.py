"""Contract tests for 017 attribution output shape from DynamicHelm (T025)."""

from __future__ import annotations

from pathlib import Path

import pytest

from eigenhelm.attribution.constants import DIMENSION_NAMES
from eigenhelm.attribution.models import (
    AttributionResult,
    DirectAttribution,
    FeatureContribution,
    SourceLocation,
)
from eigenhelm.helm import DynamicHelm
from eigenhelm.helm.models import EvaluationRequest, EvaluationResponse

pytestmark = [pytest.mark.contract, pytest.mark.requires_model]

_MODEL_PATH = Path("models/general-polyglot-v1.npz")

_FIBONACCI_SOURCE = """\
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""

# Expected method per dimension (canonical order from DIMENSION_NAMES).
_EXPECTED_METHODS: dict[str, str] = {
    "manifold_drift": "pca_reconstruction",
    "manifold_alignment": "pca_alignment",
    "token_entropy": "direct",
    "compression_structure": "direct",
    "ncd_exemplar_distance": "direct",
}


@pytest.fixture(scope="module")
def evaluation_response(polyglot_model) -> EvaluationResponse:
    """Run a real evaluation with the polyglot model."""
    helm = DynamicHelm(eigenspace=polyglot_model)
    return helm.evaluate(
        EvaluationRequest(
            source=_FIBONACCI_SOURCE,
            language="python",
        )
    )


class TestAttributionOutputContract:
    """Verify attribution shape returned by DynamicHelm.evaluate()."""

    def test_attribution_not_none_with_model(
        self, evaluation_response: EvaluationResponse
    ):
        """(a) attribution field is populated when a model is loaded."""
        assert evaluation_response.attribution is not None

    def test_attribution_is_attribution_result(
        self, evaluation_response: EvaluationResponse
    ):
        """Carrier is a single attribution object on EvaluationResponse."""
        attr = evaluation_response.attribution
        assert isinstance(attr, AttributionResult)

    def test_dimensions_count(self, evaluation_response: EvaluationResponse):
        """(b) attribution.dimensions has exactly 5 entries."""
        attr = evaluation_response.attribution
        assert attr is not None
        assert len(attr.dimensions) == 5

    def test_dimension_names_match_canonical(
        self, evaluation_response: EvaluationResponse
    ):
        """Dimensions use the canonical names from DIMENSION_NAMES."""
        attr = evaluation_response.attribution
        assert attr is not None
        actual_names = tuple(d.dimension for d in attr.dimensions)
        assert actual_names == DIMENSION_NAMES

    def test_dimension_methods(self, evaluation_response: EvaluationResponse):
        """(c) Each dimension has the correct method string."""
        attr = evaluation_response.attribution
        assert attr is not None
        for dim in attr.dimensions:
            expected = _EXPECTED_METHODS[dim.dimension]
            assert dim.method == expected, (
                f"Dimension {dim.dimension!r}: expected method {expected!r}, got {dim.method!r}"
            )

    def test_drift_features_have_contribution_fields(
        self, evaluation_response: EvaluationResponse
    ):
        """(d) PCA drift features have contribution_value and magnitude."""
        attr = evaluation_response.attribution
        assert attr is not None
        drift = next(d for d in attr.dimensions if d.dimension == "manifold_drift")
        assert len(drift.features) > 0, (
            "Drift dimension should have feature contributions"
        )
        for feat in drift.features:
            assert isinstance(feat, FeatureContribution)
            assert isinstance(feat.contribution_value, float)
            assert isinstance(feat.contribution_magnitude, float)

    def test_direct_dims_have_direct_attribution(
        self, evaluation_response: EvaluationResponse
    ):
        """(e) Direct dimensions have DirectAttribution with required fields."""
        attr = evaluation_response.attribution
        assert attr is not None
        direct_dims = [d for d in attr.dimensions if d.method == "direct"]
        assert len(direct_dims) == 3, "Expected 3 direct dimensions"
        for dim in direct_dims:
            assert dim.direct is not None, (
                f"Dimension {dim.dimension!r} should have direct attribution"
            )
            assert isinstance(dim.direct, DirectAttribution)
            assert isinstance(dim.direct.metric_name, str)
            assert len(dim.direct.metric_name) > 0
            assert isinstance(dim.direct.computed_value, float)
            assert isinstance(dim.direct.normalization, str)
            assert len(dim.direct.normalization) > 0

    def test_source_location_on_available_dims(
        self, evaluation_response: EvaluationResponse
    ):
        """(f) source_location present on available dimensions."""
        attr = evaluation_response.attribution
        assert attr is not None
        for dim in attr.dimensions:
            if dim.available:
                assert dim.source_location is not None, (
                    f"Available dimension {dim.dimension!r} should have source_location"
                )
                assert isinstance(dim.source_location, SourceLocation)
                assert dim.source_location.start_line >= 1
                assert dim.source_location.end_line >= dim.source_location.start_line

    def test_carrier_is_single_attribution_field(
        self, evaluation_response: EvaluationResponse
    ):
        """(g) Attribution is carried as a single field, not separate fields."""
        # Verify the field exists on the response dataclass itself
        assert hasattr(evaluation_response, "attribution")
        # Verify it is the sole attribution carrier (no scattered fields)
        attr = evaluation_response.attribution
        assert isinstance(attr, AttributionResult)
        # All dimension data lives inside attribution, not on the response
        assert hasattr(attr, "dimensions")
        assert hasattr(attr, "directives")

    def test_attribution_metadata_fields(self, evaluation_response: EvaluationResponse):
        """AttributionResult carries metadata: top_n, directive_threshold, vocabulary_version."""
        attr = evaluation_response.attribution
        assert attr is not None
        assert isinstance(attr.top_n, int)
        assert attr.top_n > 0
        assert isinstance(attr.directive_threshold, float)
        assert 0.0 < attr.directive_threshold < 1.0
        assert isinstance(attr.vocabulary_version, str)
        assert len(attr.vocabulary_version) > 0

    def test_directives_are_tuple(self, evaluation_response: EvaluationResponse):
        """Directives field is a tuple (possibly empty)."""
        attr = evaluation_response.attribution
        assert attr is not None
        assert isinstance(attr.directives, tuple)

    def test_normalized_scores_in_range(self, evaluation_response: EvaluationResponse):
        """All dimension normalized_score values are in [0.0, 1.0]."""
        attr = evaluation_response.attribution
        assert attr is not None
        for dim in attr.dimensions:
            assert 0.0 <= dim.normalized_score <= 1.0, (
                f"Dimension {dim.dimension!r}: normalized_score {dim.normalized_score} out of range"
            )

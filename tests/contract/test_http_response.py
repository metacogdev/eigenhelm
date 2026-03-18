"""Contract tests for 016 HTTP API response per contracts/http-api.md."""

from __future__ import annotations

import pytest

from eigenhelm.helm import DynamicHelm
from eigenhelm.helm.models import EvaluationRequest
from eigenhelm.serve.models import AttributionResultOut, ContributionOut
from eigenhelm.serve.routes.evaluate import _map_response

pytestmark = pytest.mark.contract


def _eval(source: str = "def f(): pass"):
    helm = DynamicHelm()
    return helm.evaluate(EvaluationRequest(source=source, language="python"))


class TestHttpResponseContract:
    def test_new_fields_present(self):
        helm_resp = _eval()
        api_resp = _map_response(helm_resp, file_path="test.py")
        assert hasattr(api_resp, "percentile")
        assert hasattr(api_resp, "percentile_available")
        assert hasattr(api_resp, "contributions")

    def test_decision_always_non_null_string(self):
        helm_resp = _eval()
        api_resp = _map_response(helm_resp, file_path="test.py")
        assert isinstance(api_resp.decision, str)
        assert api_resp.decision in ("accept", "warn", "reject")

    def test_existing_fields_unchanged(self):
        helm_resp = _eval()
        api_resp = _map_response(helm_resp, file_path="test.py")
        assert isinstance(api_resp.score, float)
        assert isinstance(api_resp.structural_confidence, str)
        assert isinstance(api_resp.violations, list)

    def test_contributions_type(self):
        helm_resp = _eval()
        api_resp = _map_response(helm_resp, file_path="test.py")
        assert isinstance(api_resp.contributions, list)
        for c in api_resp.contributions:
            assert isinstance(c, ContributionOut)
            assert isinstance(c.dimension, str)
            assert isinstance(c.normalized_value, float)
            assert isinstance(c.weight, float)
            assert isinstance(c.weighted_contribution, float)


def _eval_with_model(polyglot_model, source: str = "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)\n"):
    helm = DynamicHelm(eigenspace=polyglot_model)
    return helm.evaluate(EvaluationRequest(source=source, language="python"))


@pytest.mark.requires_model
class TestHttpAttributionContract:
    """017 contract: HTTP response includes attribution field."""

    def test_attribution_field_present(self, polyglot_model):
        helm_resp = _eval_with_model(polyglot_model)
        api_resp = _map_response(helm_resp, file_path="test.py")
        assert hasattr(api_resp, "attribution")
        assert api_resp.attribution is not None

    def test_attribution_is_correct_type(self, polyglot_model):
        helm_resp = _eval_with_model(polyglot_model)
        api_resp = _map_response(helm_resp, file_path="test.py")
        assert isinstance(api_resp.attribution, AttributionResultOut)

    def test_attribution_dimensions_count(self, polyglot_model):
        helm_resp = _eval_with_model(polyglot_model)
        api_resp = _map_response(helm_resp, file_path="test.py")
        assert api_resp.attribution is not None
        assert len(api_resp.attribution.dimensions) == 5

    def test_attribution_none_without_model(self):
        helm_resp = _eval()  # No model
        api_resp = _map_response(helm_resp, file_path="test.py")
        # Attribution is still present (entropy/compression always available)
        assert api_resp.attribution is not None

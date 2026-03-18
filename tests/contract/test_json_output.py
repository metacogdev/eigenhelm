"""Contract tests for 016/017 JSON output format per contracts/json-sarif.md."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from eigenhelm.cli.evaluate import format_results_json
from eigenhelm.helm import DynamicHelm
from eigenhelm.helm.models import EvaluationRequest

pytestmark = pytest.mark.contract

_MODEL_PATH = Path("models/general-polyglot-v1.npz")

_FIBONACCI_SOURCE = """\
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""


def _eval(source: str = "def f(): pass"):
    helm = DynamicHelm()
    return helm.evaluate(EvaluationRequest(source=source, language="python"))


def _eval_with_model(polyglot_model, source: str = _FIBONACCI_SOURCE):
    helm = DynamicHelm(eigenspace=polyglot_model)
    return helm.evaluate(EvaluationRequest(source=source, language="python"))


class TestJsonOutputContract:
    def test_new_fields_present(self):
        resp = _eval()
        data = json.loads(format_results_json([(Path("test.py"), resp)]))
        r = data["results"][0]
        assert "percentile" in r
        assert "percentile_available" in r
        assert "contributions" in r

    def test_decision_always_non_null_string(self):
        resp = _eval()
        data = json.loads(format_results_json([(Path("test.py"), resp)]))
        r = data["results"][0]
        assert isinstance(r["decision"], str)
        assert r["decision"] in ("accept", "warn", "reject")

    def test_existing_fields_preserved(self):
        resp = _eval()
        data = json.loads(format_results_json([(Path("test.py"), resp)]))
        r = data["results"][0]
        assert "score" in r
        assert "structural_confidence" in r
        assert "violations" in r
        assert "file_path" in r

    def test_contributions_shape(self):
        resp = _eval()
        data = json.loads(format_results_json([(Path("test.py"), resp)]))
        contributions = data["results"][0]["contributions"]
        assert isinstance(contributions, list)
        if contributions:
            c = contributions[0]
            assert "dimension" in c
            assert "normalized_value" in c
            assert "weight" in c
            assert "weighted_contribution" in c

    def test_summary_unchanged(self):
        resp = _eval()
        data = json.loads(format_results_json([(Path("test.py"), resp)]))
        summary = data["summary"]
        assert "overall_decision" in summary
        assert "total_files" in summary
        assert "mean_score" in summary


@pytest.mark.requires_model
class TestJsonAttributionOutput:
    """017 contract: JSON output includes attribution data."""

    def test_attribution_key_present(self, polyglot_model):
        """JSON result dict includes 'attribution' key."""
        resp = _eval_with_model(polyglot_model)
        data = json.loads(format_results_json([(Path("test.py"), resp)]))
        r = data["results"][0]
        assert "attribution" in r, "JSON output must include 'attribution' key"

    def test_attribution_has_dimensions_array(self, polyglot_model):
        """Attribution object contains a 'dimensions' array."""
        resp = _eval_with_model(polyglot_model)
        data = json.loads(format_results_json([(Path("test.py"), resp)]))
        attr = data["results"][0]["attribution"]
        assert isinstance(attr, dict)
        assert "dimensions" in attr
        assert isinstance(attr["dimensions"], list)

    def test_attribution_has_directives_array(self, polyglot_model):
        """Attribution object contains a 'directives' array."""
        resp = _eval_with_model(polyglot_model)
        data = json.loads(format_results_json([(Path("test.py"), resp)]))
        attr = data["results"][0]["attribution"]
        assert "directives" in attr
        assert isinstance(attr["directives"], list)

    def test_attribution_dimensions_count(self, polyglot_model):
        """Attribution dimensions array has exactly 5 entries."""
        resp = _eval_with_model(polyglot_model)
        data = json.loads(format_results_json([(Path("test.py"), resp)]))
        dims = data["results"][0]["attribution"]["dimensions"]
        assert len(dims) == 5

    def test_attribution_dimension_shape(self, polyglot_model):
        """Each attribution dimension has required keys."""
        resp = _eval_with_model(polyglot_model)
        data = json.loads(format_results_json([(Path("test.py"), resp)]))
        dims = data["results"][0]["attribution"]["dimensions"]
        for dim in dims:
            assert "dimension" in dim
            assert "normalized_score" in dim
            assert "method" in dim
            assert "available" in dim

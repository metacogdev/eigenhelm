"""Contract tests for 016/017 SARIF output format per contracts/json-sarif.md."""

from __future__ import annotations

from pathlib import Path

import pytest

from eigenhelm.helm import DynamicHelm
from eigenhelm.helm.models import EvaluationRequest
from eigenhelm.output.sarif import build_sarif

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


class TestSarifOutputContract:
    def test_properties_contain_new_fields(self):
        resp = _eval()
        sarif = build_sarif([(Path("test.py"), resp)], tool_version="0.1.0")
        props = sarif["runs"][0]["results"][0]["properties"]
        assert "percentile" in props
        assert "percentile_available" in props
        assert "contributions" in props

    def test_contributions_shape(self):
        resp = _eval()
        sarif = build_sarif([(Path("test.py"), resp)], tool_version="0.1.0")
        contributions = sarif["runs"][0]["results"][0]["properties"]["contributions"]
        assert isinstance(contributions, list)
        if contributions:
            c = contributions[0]
            assert "dimension" in c
            assert "normalized_value" in c
            assert "weight" in c
            assert "weighted_contribution" in c

    def test_level_mapping_unchanged(self):
        for decision, expected_level in [
            ("accept", "note"),
            ("warn", "warning"),
            ("reject", "error"),
        ]:
            from dataclasses import replace

            resp = replace(_eval(), decision=decision)
            sarif = build_sarif([(Path("test.py"), resp)], tool_version="0.1.0")
            result = sarif["runs"][0]["results"][0]
            assert result["level"] == expected_level

    def test_message_text_with_unavailable_percentile(self):
        resp = _eval()  # No model → percentile unavailable
        sarif = build_sarif([(Path("test.py"), resp)], tool_version="0.1.0")
        msg = sarif["runs"][0]["results"][0]["message"]["text"]
        # Contract: "Score: <S> [<decision>]" format when percentile unavailable
        assert "Score:" in msg
        assert f"[{resp.decision}]" in msg


@pytest.mark.requires_model
class TestSarifAttributionOutput:
    """017 contract: SARIF output includes attribution data."""

    def test_attribution_in_properties(self, polyglot_model):
        """(a) attribution key present in result properties."""
        resp = _eval_with_model(polyglot_model)
        sarif = build_sarif([(Path("test.py"), resp)], tool_version="0.1.0")
        props = sarif["runs"][0]["results"][0]["properties"]
        assert "attribution" in props, "SARIF properties must include 'attribution' key"

    def test_attribution_dimensions_count(self, polyglot_model):
        """(d) attribution dimensions array has 5 entries."""
        resp = _eval_with_model(polyglot_model)
        sarif = build_sarif([(Path("test.py"), resp)], tool_version="0.1.0")
        attr = sarif["runs"][0]["results"][0]["properties"]["attribution"]
        assert isinstance(attr, dict)
        assert "dimensions" in attr
        assert len(attr["dimensions"]) == 5

    def test_directive_rule_id_format(self, polyglot_model):
        """(b) directive results have ruleId matching eigenhelm/directive/{category}."""
        resp = _eval_with_model(polyglot_model)
        sarif = build_sarif([(Path("test.py"), resp)], tool_version="0.1.0")
        results = sarif["runs"][0]["results"]
        # Find directive results (those beyond the main aesthetic-score result)
        directive_results = [
            r for r in results if r["ruleId"].startswith("eigenhelm/directive/")
        ]
        # If there are directives in attribution, they should appear as SARIF results
        attr = resp.attribution
        if attr is not None and len(attr.directives) > 0:
            assert len(directive_results) > 0, (
                "Directives in attribution should produce SARIF results"
            )
            for dr in directive_results:
                rule_id = dr["ruleId"]
                assert rule_id.startswith("eigenhelm/directive/"), (
                    f"Directive ruleId {rule_id!r} must start with 'eigenhelm/directive/'"
                )
                # Category is the part after the prefix
                category = rule_id.removeprefix("eigenhelm/directive/")
                assert len(category) > 0

    def test_directive_results_have_physical_location(self, polyglot_model):
        """(c) directive results include physicalLocation with region lines."""
        resp = _eval_with_model(polyglot_model)
        sarif = build_sarif([(Path("test.py"), resp)], tool_version="0.1.0")
        results = sarif["runs"][0]["results"]
        directive_results = [
            r for r in results if r["ruleId"].startswith("eigenhelm/directive/")
        ]
        attr = resp.attribution
        if attr is not None and len(attr.directives) > 0:
            assert len(directive_results) > 0
            for dr in directive_results:
                locations = dr.get("locations", [])
                assert len(locations) > 0, "Directive result must have locations"
                phys = locations[0]["physicalLocation"]
                region = phys["region"]
                assert "startLine" in region
                assert "endLine" in region
                assert region["startLine"] >= 1
                assert region["endLine"] >= region["startLine"]

    def test_attribution_dimensions_shape(self, polyglot_model):
        """Each attribution dimension in SARIF has required keys."""
        resp = _eval_with_model(polyglot_model)
        sarif = build_sarif([(Path("test.py"), resp)], tool_version="0.1.0")
        attr = sarif["runs"][0]["results"][0]["properties"]["attribution"]
        for dim in attr["dimensions"]:
            assert "dimension" in dim
            assert "normalized_score" in dim
            assert "method" in dim
            assert "available" in dim

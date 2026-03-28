"""Contract tests for region output formatting (019-test-code-split).

Validates invariants from contracts/region-output.md.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

_FIXTURES = Path(__file__).parent.parent / "fixtures" / "regions"


@pytest.fixture
def helm():
    from eigenhelm.eigenspace import load_model
    from eigenhelm.helm import DynamicHelm
    from eigenhelm.trained_models import default_model_path

    model = load_model(str(default_model_path()))
    return DynamicHelm(eigenspace=model)


def _evaluate_with_regions(helm, fixture_name, language):
    from eigenhelm.cli.evaluate import _attach_regions
    from eigenhelm.helm.models import EvaluationRequest

    source = (_FIXTURES / fixture_name).read_text()
    resp = helm.evaluate(EvaluationRequest(source=source, language=language))
    return _attach_regions(resp, source, language, helm)


# ---------------------------------------------------------------------------
# JSON output contracts
# ---------------------------------------------------------------------------


@pytest.mark.requires_model
def test_json_regions_present_when_test_code(helm):
    """Invariant 1: regions key present when test code detected."""
    from eigenhelm.output.json_format import format_results_json

    resp = _evaluate_with_regions(helm, "python_with_tests.py", "python")
    output = json.loads(format_results_json([("test.py", resp)]))
    assert "regions" in output["results"][0]


@pytest.mark.requires_model
def test_json_regions_absent_when_no_test_code(helm):
    """Invariant 1 (converse): regions key absent for no-test files."""
    from eigenhelm.output.json_format import format_results_json

    resp = _evaluate_with_regions(helm, "python_no_tests.py", "python")
    output = json.loads(format_results_json([("test.py", resp)]))
    assert "regions" not in output["results"][0]


@pytest.mark.requires_model
def test_json_region_uses_warn_not_marginal(helm):
    """Invariant: decision field uses 'warn', not 'marginal'."""
    from eigenhelm.output.json_format import format_results_json

    resp = _evaluate_with_regions(helm, "python_with_tests.py", "python")
    output = json.loads(format_results_json([("test.py", resp)]))
    for region in output["results"][0]["regions"]:
        assert region["decision"] in ("accept", "warn", "reject")
        assert region["decision"] != "marginal"


@pytest.mark.requires_model
def test_json_region_has_required_fields(helm):
    """Each region entry has label, spans, total_lines, score, decision."""
    from eigenhelm.output.json_format import format_results_json

    resp = _evaluate_with_regions(helm, "python_with_tests.py", "python")
    output = json.loads(format_results_json([("test.py", resp)]))
    for region in output["results"][0]["regions"]:
        assert "label" in region
        assert "spans" in region
        assert "total_lines" in region
        assert "score" in region
        assert "decision" in region
        assert region["label"] in ("production", "test")


# ---------------------------------------------------------------------------
# SARIF output contracts
# ---------------------------------------------------------------------------


@pytest.mark.requires_model
def test_sarif_properties_regions_present(helm):
    """Invariant 6: SARIF includes properties.regions on file-level result."""
    from eigenhelm.output.sarif import build_sarif

    resp = _evaluate_with_regions(helm, "python_with_tests.py", "python")
    sarif = build_sarif([("test.py", resp)], tool_version="test")

    # Find the file-level result (ruleId starts with eigenhelm/)
    results = sarif["runs"][0]["results"]
    file_results = [
        r
        for r in results
        if r.get("ruleId", "").startswith("eigenhelm/aesthetic-score")
    ]
    assert len(file_results) >= 1

    file_result = file_results[0]
    assert "properties" in file_result
    assert "regions" in file_result["properties"]


@pytest.mark.requires_model
def test_sarif_no_properties_regions_when_no_tests(helm):
    """No properties.regions when no test code detected."""
    from eigenhelm.output.sarif import build_sarif

    resp = _evaluate_with_regions(helm, "python_no_tests.py", "python")
    sarif = build_sarif([("test.py", resp)], tool_version="test")

    results = sarif["runs"][0]["results"]
    file_results = [
        r
        for r in results
        if r.get("ruleId", "").startswith("eigenhelm/aesthetic-score")
    ]
    for fr in file_results:
        props = fr.get("properties", {})
        assert "regions" not in props

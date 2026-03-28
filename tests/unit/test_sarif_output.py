"""Unit tests for SARIF output generation."""

from __future__ import annotations

import json
from pathlib import Path


from eigenhelm.output.sarif import (
    SARIF_SCHEMA,
    SARIF_VERSION,
    build_sarif,
    format_sarif,
)


def _make_response(decision="accept", score=0.2):
    """Build a minimal EvaluationResponse for testing."""
    from eigenhelm.helm import DynamicHelm, EvaluationRequest

    helm = DynamicHelm()
    # Use a short snippet to get a deterministic-ish response, then override fields
    resp = helm.evaluate(EvaluationRequest(source="def f(): pass", language="python"))
    # We can't mutate frozen dataclasses, so we test with real responses
    return resp


class TestBuildSarif:
    def test_document_version(self):
        doc = build_sarif([], tool_version="1.0.0")
        assert doc["version"] == SARIF_VERSION

    def test_document_schema(self):
        doc = build_sarif([], tool_version="1.0.0")
        assert doc["$schema"] == SARIF_SCHEMA

    def test_tool_driver_name(self):
        doc = build_sarif([], tool_version="0.5.0")
        driver = doc["runs"][0]["tool"]["driver"]
        assert driver["name"] == "eigenhelm"
        assert driver["version"] == "0.5.0"

    def test_tool_driver_rules_present(self):
        doc = build_sarif([], tool_version="1.0.0")
        rules = doc["runs"][0]["tool"]["driver"]["rules"]
        assert len(rules) > 0
        rule_ids = [r["id"] for r in rules]
        assert "eigenhelm/aesthetic-score" in rule_ids

    def test_invocations(self):
        doc = build_sarif([], tool_version="1.0.0")
        inv = doc["runs"][0]["invocations"]
        assert len(inv) == 1
        assert inv[0]["executionSuccessful"] is True

    def test_empty_results(self):
        doc = build_sarif([], tool_version="1.0.0")
        assert doc["runs"][0]["results"] == []

    def test_result_count_matches_files(self):
        resp = _make_response()
        doc = build_sarif(
            [("file1.py", resp), ("file2.py", resp)],
            tool_version="1.0.0",
        )
        main_results = [
            r
            for r in doc["runs"][0]["results"]
            if r["ruleId"] == "eigenhelm/aesthetic-score"
        ]
        assert len(main_results) == 2

    def test_result_has_rule_id(self):
        resp = _make_response()
        doc = build_sarif([("file.py", resp)], tool_version="1.0.0")
        result = doc["runs"][0]["results"][0]
        assert "ruleId" in result
        assert result["ruleId"] == "eigenhelm/aesthetic-score"

    def test_result_has_message(self):
        resp = _make_response()
        doc = build_sarif([("file.py", resp)], tool_version="1.0.0")
        result = doc["runs"][0]["results"][0]
        assert "message" in result
        assert "text" in result["message"]

    def test_result_has_location(self):
        resp = _make_response()
        doc = build_sarif([("src/file.py", resp)], tool_version="1.0.0")
        result = doc["runs"][0]["results"][0]
        assert "locations" in result
        loc = result["locations"][0]
        artifact_uri = loc["physicalLocation"]["artifactLocation"]["uri"]
        assert "file.py" in artifact_uri

    def test_accept_maps_to_note(self):
        from eigenhelm.helm import DynamicHelm, EvaluationRequest

        helm = DynamicHelm()
        # Evaluate simple code that should score accept
        resp = helm.evaluate(EvaluationRequest(source="x = 1\n", language="python"))
        # Accept maps to note level
        if resp.decision == "accept":
            doc = build_sarif([("f.py", resp)], tool_version="1.0.0")
            assert doc["runs"][0]["results"][0]["level"] == "note"

    def test_level_mapping_coverage(self):
        """Test all three decision/level mappings using mock responses."""
        from unittest.mock import MagicMock

        # Create mock responses with specific decisions
        for decision, expected_level in [
            ("accept", "note"),
            ("warn", "warning"),
            ("reject", "error"),
        ]:
            mock_resp = MagicMock()
            mock_resp.decision = decision
            mock_resp.score = 0.5
            mock_resp.structural_confidence = "low"
            mock_resp.critique.violations = []
            mock_resp.attribution = None

            doc = build_sarif([("file.py", mock_resp)], tool_version="1.0.0")
            result = doc["runs"][0]["results"][0]
            assert result["level"] == expected_level, (
                f"Expected {expected_level} for decision={decision}"
            )

    def test_result_properties_contain_score(self):
        resp = _make_response()
        doc = build_sarif([("file.py", resp)], tool_version="1.0.0")
        result = doc["runs"][0]["results"][0]
        assert "properties" in result
        assert "score" in result["properties"]
        assert "decision" in result["properties"]

    def test_path_object_works(self):
        resp = _make_response()
        doc = build_sarif([(Path("src/module.py"), resp)], tool_version="1.0.0")
        main_results = [
            r
            for r in doc["runs"][0]["results"]
            if r["ruleId"] == "eigenhelm/aesthetic-score"
        ]
        assert len(main_results) == 1


class TestFormatSarif:
    def test_returns_valid_json(self):
        resp = _make_response()
        output = format_sarif([("file.py", resp)], tool_version="1.0.0")
        data = json.loads(output)
        assert data["version"] == SARIF_VERSION

    def test_pretty_printed(self):
        output = format_sarif([], tool_version="1.0.0")
        assert "\n" in output  # Pretty-printed with indent=2

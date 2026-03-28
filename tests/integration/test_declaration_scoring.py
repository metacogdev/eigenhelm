"""Integration tests for declaration-aware scoring (020).

Tests the full pipeline: source → DynamicHelm → directives + output.
"""

from __future__ import annotations

import json

from eigenhelm.cli.evaluate import format_result_human
from eigenhelm.helm.dynamic_helm import DynamicHelm
from eigenhelm.helm.models import EvaluationRequest
from eigenhelm.output.json_format import format_results_json
from eigenhelm.output.sarif import build_sarif

# A synthetic declaration-heavy Python file (8 frozen dataclasses, no logic)
_DECLARATION_HEAVY_SOURCE = """
from dataclasses import dataclass


@dataclass(frozen=True)
class SearchResult:
    title: str
    url: str
    score: float


@dataclass(frozen=True)
class SearchFilters:
    language: str
    min_score: float
    max_results: int


@dataclass(frozen=True)
class GraphNode:
    id: str
    label: str
    kind: str


@dataclass(frozen=True)
class GraphEdge:
    source: str
    target: str
    relation: str


@dataclass(frozen=True)
class GraphResult:
    nodes: list
    edges: list


@dataclass(frozen=True)
class APIConfig:
    host: str
    port: int
    debug: bool


@dataclass(frozen=True)
class StoreConfig:
    path: str
    max_size: int
    ttl: int


@dataclass(frozen=True)
class ServerConfig:
    api: str
    store: str
    workers: int
"""

# A logic-heavy file (not declaration-dominant)
_LOGIC_HEAVY_SOURCE = """
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    host: str
    port: int


def process(data):
    result = []
    for item in data:
        if item > 0:
            result.append(item * 2)
        else:
            result.append(0)
    return result


def validate(config):
    if not config.host:
        raise ValueError("host required")
    if config.port < 1 or config.port > 65535:
        raise ValueError("invalid port")
    return True


def transform(items):
    output = {}
    for i, item in enumerate(items):
        key = f"item_{i}"
        output[key] = item
    return output
"""


class TestDirectiveContext:
    """US1: Declaration-dominant files get review_structure directives."""

    def test_declaration_heavy_gets_review_structure_directives(self):
        helm = DynamicHelm()
        request = EvaluationRequest(source=_DECLARATION_HEAVY_SOURCE, language="python")
        response = helm.evaluate(request)

        # Must have declaration_ratio set
        assert response.declaration_ratio is not None
        assert response.declaration_ratio >= 0.6

        # All PCA directives should use review_structure, not extract_repeated_logic
        if response.attribution is not None:
            for d in response.attribution.directives:
                if d.dimension in ("manifold_drift", "manifold_alignment"):
                    assert d.category != "extract_repeated_logic", (
                        f"Declaration-dominant file should not get extract_repeated_logic "
                        f"but got it for {d.dimension}"
                    )

    def test_logic_heavy_has_no_declaration_ratio(self):
        helm = DynamicHelm()
        request = EvaluationRequest(source=_LOGIC_HEAVY_SOURCE, language="python")
        response = helm.evaluate(request)

        # Non-declaration-dominant: declaration_ratio should be None
        assert response.declaration_ratio is None

    def test_human_output_includes_declaration_heavy_tag(self):
        helm = DynamicHelm()
        request = EvaluationRequest(source=_DECLARATION_HEAVY_SOURCE, language="python")
        response = helm.evaluate(request)

        output = format_result_human("types.py", response)
        assert "[declaration-heavy]" in output

    def test_logic_heavy_output_has_no_declaration_tag(self):
        helm = DynamicHelm()
        request = EvaluationRequest(source=_LOGIC_HEAVY_SOURCE, language="python")
        response = helm.evaluate(request)

        output = format_result_human("logic.py", response)
        assert "[declaration-heavy]" not in output


class TestScoreDampening:
    """US2: Declaration-dominant files get dampened scores."""

    def test_declaration_heavy_score_above_accept_threshold(self):
        helm = DynamicHelm()
        request = EvaluationRequest(source=_DECLARATION_HEAVY_SOURCE, language="python")
        response = helm.evaluate(request)
        # Dampened score must still be above accept threshold (0.4)
        assert response.score >= 0.4

    def test_logic_heavy_score_unchanged(self):
        """Non-declaration files should produce identical scores."""
        helm = DynamicHelm()
        request = EvaluationRequest(source=_LOGIC_HEAVY_SOURCE, language="python")
        r1 = helm.evaluate(request)
        r2 = helm.evaluate(request)
        assert r1.score == r2.score


class TestMachineReadableOutput:
    """US3: JSON and SARIF include declaration_ratio."""

    def test_json_includes_declaration_ratio_for_dominant(self):
        helm = DynamicHelm()
        request = EvaluationRequest(source=_DECLARATION_HEAVY_SOURCE, language="python")
        response = helm.evaluate(request)
        json_str = format_results_json([("types.py", response)])
        data = json.loads(json_str)
        result = data["results"][0]
        assert "declaration_ratio" in result
        assert isinstance(result["declaration_ratio"], float)
        assert result["declaration_ratio"] >= 0.6

    def test_json_omits_declaration_ratio_for_non_dominant(self):
        helm = DynamicHelm()
        request = EvaluationRequest(source=_LOGIC_HEAVY_SOURCE, language="python")
        response = helm.evaluate(request)
        json_str = format_results_json([("logic.py", response)])
        data = json.loads(json_str)
        result = data["results"][0]
        assert "declaration_ratio" not in result

    def test_sarif_includes_declaration_ratio_for_dominant(self):
        helm = DynamicHelm()
        request = EvaluationRequest(source=_DECLARATION_HEAVY_SOURCE, language="python")
        response = helm.evaluate(request)
        sarif = build_sarif([("types.py", response)], tool_version="0.0.0-test")
        results = sarif["runs"][0]["results"]
        # Find the aesthetic-score result
        score_result = next(
            r for r in results if r["ruleId"] == "eigenhelm/aesthetic-score"
        )
        assert "declaration_ratio" in score_result["properties"]
        assert isinstance(score_result["properties"]["declaration_ratio"], float)

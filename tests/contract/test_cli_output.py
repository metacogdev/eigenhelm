"""Contract tests for 016 CLI output formats per contracts/cli-output.md."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from eigenhelm.cli.evaluate import (
    format_ranking_human,
    format_result_human,
    format_summary_human,
)
from eigenhelm.helm import DynamicHelm
from eigenhelm.helm.models import EvaluationRequest

pytestmark = pytest.mark.contract


def _eval_source(source: str = "def f(): pass", language: str = "python"):
    """Helper: evaluate source through real pipeline (no model)."""
    helm = DynamicHelm()
    return helm.evaluate(EvaluationRequest(source=source, language=language))


# ---------------------------------------------------------------------------
# Default mode (T014)
# ---------------------------------------------------------------------------


class TestDefaultModeContract:
    def test_score_line_format(self):
        resp = _eval_source()
        output = format_result_human(Path("test.py"), resp)
        assert "score:" in output

    def test_percentile_unavailable_fallback(self):
        resp = _eval_source()
        output = format_result_human(Path("test.py"), resp)
        assert "percentile unavailable" in output
        assert "retrain model for percentile data" in output

    def test_contributions_present(self):
        resp = _eval_source()
        output = format_result_human(Path("test.py"), resp)
        assert "contributions:" in output

    def test_contribution_line_format(self):
        resp = _eval_source()
        output = format_result_human(Path("test.py"), resp)
        # Should show weight and normalized values
        assert "weight:" in output
        assert "normalized:" in output

    def test_no_decision_in_default_mode(self):
        resp = _eval_source()
        output = format_result_human(Path("test.py"), resp)
        assert "decision:" not in output


# ---------------------------------------------------------------------------
# Summary format (T014)
# ---------------------------------------------------------------------------


class TestSummaryContract:
    def test_summary_format(self):
        resp1 = _eval_source("def f(): pass")
        resp2 = _eval_source("def g(): return 42")
        results = [(Path("a.py"), resp1), (Path("b.py"), resp2)]
        summary = format_summary_human(results)
        assert "Summary:" in summary
        assert "mean score:" in summary
        assert "2 files" in summary

    def test_summary_no_percentile_without_model(self):
        resp = _eval_source()
        summary = format_summary_human([(Path("a.py"), resp)])
        # No model → no percentile in summary
        assert "mean percentile" not in summary


# ---------------------------------------------------------------------------
# Ranking mode (T021)
# ---------------------------------------------------------------------------


class TestRankingModeContract:
    def test_ranking_header(self):
        results = [
            (Path("a.py"), _eval_source("def a(): pass")),
            (Path("b.py"), _eval_source("def b(): return 42")),
            (Path("c.py"), _eval_source("import os\ndef c(): return os.getcwd()")),
        ]
        output = format_ranking_human(results)
        assert "Ranking:" in output
        assert "files evaluated" in output

    def test_ranking_numbered_rows(self):
        results = [
            (Path("a.py"), _eval_source("def a(): pass")),
            (Path("b.py"), _eval_source("def b(): return 42")),
        ]
        output = format_ranking_human(results)
        assert "#1" in output
        assert "#2" in output

    def test_ranking_spread_footer(self):
        results = [
            (Path("a.py"), _eval_source("def a(): pass")),
            (Path("b.py"), _eval_source("def b(): return 42")),
        ]
        output = format_ranking_human(results)
        assert "spread:" in output
        assert "highlighted:" in output

    def test_single_file_fallback(self):
        results = [(Path("a.py"), _eval_source("def a(): pass"))]
        output = format_ranking_human(results)
        assert "relative ranking requires multiple files" in output


# ---------------------------------------------------------------------------
# Classification mode (T024)
# ---------------------------------------------------------------------------


class TestClassificationModeContract:
    def test_decision_label_present(self):
        resp = _eval_source()
        output = format_result_human(Path("test.py"), resp, classify=True)
        assert "decision:" in output

    def test_marginal_vocabulary(self):
        resp = _eval_source()
        resp = replace(resp, decision="warn")
        output = format_result_human(Path("test.py"), resp, classify=True)
        assert "decision: marginal" in output

    def test_percentile_coexists_with_classification(self):
        resp = _eval_source()
        output = format_result_human(Path("test.py"), resp, classify=True)
        assert "decision:" in output
        assert "score:" in output

    def test_classify_summary_shows_counts(self):
        resp1 = _eval_source()
        resp2 = replace(_eval_source(), decision="warn")
        results = [(Path("a.py"), resp1), (Path("b.py"), resp2)]
        summary = format_summary_human(results, classify=True)
        assert "accepted" in summary
        assert "marginal" in summary
        assert "rejected" in summary

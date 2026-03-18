"""Contract tests for eigenhelm-evaluate CLI output format flags."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from eigenhelm.cli.evaluate import main

pytestmark = pytest.mark.contract


def _make_mock_result(path="file.py", decision="accept", score=0.2):
    resp = MagicMock()
    resp.decision = decision
    resp.score = score
    resp.structural_confidence = "low"
    resp.critique.violations = []
    resp.warning = None
    resp.percentile = 80.0
    resp.percentile_available = True
    resp.contributions = ()
    resp.attribution = None
    return (path, resp)


def _run_main_capture(args, mock_results=None, capsys=None):
    """Run main() with mocked results, return (exit_code, stdout, stderr)."""
    results = mock_results or [_make_mock_result()]
    with patch("eigenhelm.cli.evaluate._evaluate_paths", return_value=results):
        code = main(args)
    if capsys:
        captured = capsys.readouterr()
        return code, captured.out, captured.err
    return code


class TestFormatJsonFlag:
    def test_format_json_produces_json(self, capsys, tmp_path):
        f = tmp_path / "file.py"
        f.write_text("x = 1\n")
        with patch(
            "eigenhelm.cli.evaluate._evaluate_paths",
            return_value=[_make_mock_result(str(f))],
        ):
            main([str(f), "--format", "json"])
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "results" in data
        assert "summary" in data

    def test_format_json_schema_has_results_array(self, capsys, tmp_path):
        f = tmp_path / "file.py"
        f.write_text("x = 1\n")
        results = [_make_mock_result(str(f))]
        with patch("eigenhelm.cli.evaluate._evaluate_paths", return_value=results):
            main([str(f), "--format", "json"])
        data = json.loads(capsys.readouterr().out)
        assert len(data["results"]) == 1
        r = data["results"][0]
        assert "decision" in r
        assert "score" in r
        assert "file_path" in r


class TestLegacyJsonFlag:
    def test_json_flag_emits_deprecation_warning(self, capsys, tmp_path):
        f = tmp_path / "file.py"
        f.write_text("x = 1\n")
        with patch(
            "eigenhelm.cli.evaluate._evaluate_paths",
            return_value=[_make_mock_result(str(f))],
        ):
            main([str(f), "--json"])
        captured = capsys.readouterr()
        assert "DEPRECATION" in captured.err
        assert "--format json" in captured.err

    def test_json_flag_produces_same_output_as_format_json(self, capsys, tmp_path):
        f = tmp_path / "file.py"
        f.write_text("x = 1\n")
        mock_results = [_make_mock_result(str(f))]

        with patch("eigenhelm.cli.evaluate._evaluate_paths", return_value=mock_results):
            main([str(f), "--json"])
        json_flag_out = capsys.readouterr().out

        with patch("eigenhelm.cli.evaluate._evaluate_paths", return_value=mock_results):
            main([str(f), "--format", "json"])
        format_flag_out = capsys.readouterr().out

        assert json.loads(json_flag_out) == json.loads(format_flag_out)

    def test_json_and_format_mutually_exclusive(self, capsys, tmp_path):
        f = tmp_path / "file.py"
        f.write_text("x = 1\n")
        code = main([str(f), "--json", "--format", "sarif"])
        assert code == 3
        assert "mutually exclusive" in capsys.readouterr().err


class TestFormatSarifFlag:
    def test_format_sarif_produces_sarif_json(self, capsys, tmp_path):
        f = tmp_path / "file.py"
        f.write_text("x = 1\n")
        with patch(
            "eigenhelm.cli.evaluate._evaluate_paths",
            return_value=[_make_mock_result(str(f))],
        ):
            main([str(f), "--format", "sarif"])
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["version"] == "2.1.0"
        assert "runs" in data

    def test_format_sarif_result_count_matches(self, capsys, tmp_path):
        f1 = tmp_path / "a.py"
        f2 = tmp_path / "b.py"
        f1.write_text("x = 1\n")
        f2.write_text("y = 2\n")
        results = [_make_mock_result(str(f1)), _make_mock_result(str(f2))]
        with patch("eigenhelm.cli.evaluate._evaluate_paths", return_value=results):
            main([str(tmp_path), "--format", "sarif"])
        data = json.loads(capsys.readouterr().out)
        assert len(data["runs"][0]["results"]) == 2


class TestHumanFormat:
    def test_default_is_human(self, capsys, tmp_path):
        f = tmp_path / "file.py"
        f.write_text("x = 1\n")
        with patch(
            "eigenhelm.cli.evaluate._evaluate_paths",
            return_value=[_make_mock_result(str(f))],
        ):
            main([str(f)])
        captured = capsys.readouterr()
        # Human format shows score with percentile (016), not JSON
        assert "score:" in captured.out
        assert "p80" in captured.out

    def test_format_human_explicit(self, capsys, tmp_path):
        f = tmp_path / "file.py"
        f.write_text("x = 1\n")
        with patch(
            "eigenhelm.cli.evaluate._evaluate_paths",
            return_value=[_make_mock_result(str(f))],
        ):
            main([str(f), "--format", "human"])
        captured = capsys.readouterr()
        assert "score:" in captured.out
        assert "confidence:" in captured.out

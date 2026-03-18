"""Unit tests for eigenhelm-evaluate CLI."""

from __future__ import annotations

import json
from pathlib import Path

from eigenhelm.cli.evaluate import (
    discover_files,
    format_result_human,
    format_results_json,
)


class TestDiscoverFiles:
    def test_single_py_file(self, tmp_path):
        f = tmp_path / "test.py"
        f.write_text("x = 1\n")
        result = discover_files([f])
        assert len(result) == 1
        assert result[0] == (f, "python")

    def test_directory_mixed_extensions(self, tmp_path):
        (tmp_path / "a.py").write_text("x = 1")
        (tmp_path / "b.js").write_text("var x = 1;")
        (tmp_path / "c.txt").write_text("hello")
        result = discover_files([tmp_path])
        languages = {lang for _, lang in result}
        assert "python" in languages
        assert "javascript" in languages
        assert len(result) == 2  # .txt skipped

    def test_unrecognized_extension_skipped(self, tmp_path):
        f = tmp_path / "test.xyz"
        f.write_text("stuff")
        result = discover_files([f])
        assert len(result) == 0

    def test_no_follow_symlinks(self, tmp_path):
        real_file = tmp_path / "real.py"
        real_file.write_text("x = 1")
        link = tmp_path / "subdir"
        link.mkdir()
        symlink = link / "link.py"
        symlink.symlink_to(real_file)
        result = discover_files([link])
        assert len(result) == 0  # symlinks are skipped


class TestFormatResultHuman:
    def test_default_mode_shows_percentile_and_contributions(self):
        from eigenhelm.helm import DynamicHelm, EvaluationRequest

        helm = DynamicHelm()
        resp = helm.evaluate(EvaluationRequest(source="def f(): pass", language="python"))
        output = format_result_human(Path("test.py"), resp)
        # Default mode: no decision label, has score + percentile info
        assert "score:" in output
        assert "confidence:" in output
        assert "contributions:" in output
        # Default mode should NOT show decision label
        assert "decision:" not in output

    def test_default_mode_without_model_shows_unavailable(self):
        from eigenhelm.helm import DynamicHelm, EvaluationRequest

        helm = DynamicHelm()  # No model → no score distribution
        resp = helm.evaluate(EvaluationRequest(source="def f(): pass", language="python"))
        output = format_result_human(Path("test.py"), resp)
        assert "percentile unavailable" in output

    def test_classify_mode_shows_decision(self):
        from eigenhelm.helm import DynamicHelm, EvaluationRequest

        helm = DynamicHelm()
        resp = helm.evaluate(EvaluationRequest(source="def f(): pass", language="python"))
        output = format_result_human(Path("test.py"), resp, classify=True)
        assert "decision:" in output
        assert "score:" in output

    def test_classify_mode_uses_marginal_vocabulary(self):
        """Machine 'warn' should display as 'marginal' in human CLI."""
        from dataclasses import replace

        from eigenhelm.helm import DynamicHelm, EvaluationRequest

        helm = DynamicHelm()
        resp = helm.evaluate(EvaluationRequest(source="def f(): pass", language="python"))
        # Force decision to 'warn' to test vocabulary mapping
        resp = replace(resp, decision="warn")
        output = format_result_human(Path("test.py"), resp, classify=True)
        assert "decision: marginal" in output
        assert "decision: warn" not in output


class TestFormatResultsJson:
    def test_valid_json_matching_schema(self):
        from eigenhelm.helm import DynamicHelm, EvaluationRequest

        helm = DynamicHelm()
        resp = helm.evaluate(EvaluationRequest(source="def f(): pass", language="python"))
        output = format_results_json([(Path("test.py"), resp)])
        data = json.loads(output)
        assert "results" in data
        assert "summary" in data
        assert len(data["results"]) == 1
        r = data["results"][0]
        assert "decision" in r
        assert "score" in r
        assert "structural_confidence" in r
        assert "violations" in r
        assert "file_path" in r

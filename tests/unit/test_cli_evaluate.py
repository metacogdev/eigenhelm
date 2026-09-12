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

    def test_config_excludes_skip_files(self, tmp_path):
        (tmp_path / "a.py").write_text("x = 1")
        (tmp_path / "b_pb2.py").write_text("x = 1")
        (tmp_path / "c.py").write_text("x = 1")
        result = discover_files([tmp_path], config_excludes=("*_pb2.py",))
        paths = [p.name for p, _ in result]
        assert "a.py" in paths
        assert "c.py" in paths
        assert "b_pb2.py" not in paths

    def test_config_excludes_skip_directories(self, tmp_path):
        vendor = tmp_path / "vendor"
        vendor.mkdir()
        (vendor / "lib.py").write_text("x = 1")
        (tmp_path / "main.py").write_text("x = 1")
        result = discover_files([tmp_path], config_excludes=("vendor",))
        paths = [p.name for p, _ in result]
        assert "main.py" in paths
        assert "lib.py" not in paths

    def test_config_excludes_glob_pattern(self, tmp_path):
        gen = tmp_path / "src" / "generated"
        gen.mkdir(parents=True)
        (gen / "out.py").write_text("x = 1")
        src = tmp_path / "src"
        (src / "app.py").write_text("x = 1")
        result = discover_files([tmp_path], config_excludes=("src/generated/**",))
        paths = [p.name for p, _ in result]
        assert "app.py" in paths
        assert "out.py" not in paths

    def test_config_excludes_explicit_file_path(self, tmp_path):
        f = tmp_path / "skip_pb2.py"
        f.write_text("x = 1")
        result = discover_files([f], config_excludes=("*_pb2.py",))
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
        resp = helm.evaluate(
            EvaluationRequest(source="def f(): pass", language="python")
        )
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
        resp = helm.evaluate(
            EvaluationRequest(source="def f(): pass", language="python")
        )
        output = format_result_human(Path("test.py"), resp)
        assert "percentile unavailable" in output

    def test_classify_mode_shows_decision(self):
        from eigenhelm.helm import DynamicHelm, EvaluationRequest

        helm = DynamicHelm()
        resp = helm.evaluate(
            EvaluationRequest(source="def f(): pass", language="python")
        )
        output = format_result_human(Path("test.py"), resp, classify=True)
        assert "decision:" in output
        assert "score:" in output

    def test_classify_mode_uses_marginal_vocabulary(self):
        """Machine 'warn' should display as 'marginal' in human CLI."""
        from dataclasses import replace

        from eigenhelm.helm import DynamicHelm, EvaluationRequest

        helm = DynamicHelm()
        resp = helm.evaluate(
            EvaluationRequest(source="def f(): pass", language="python")
        )
        # Force decision to 'warn' to test vocabulary mapping
        resp = replace(resp, decision="warn")
        output = format_result_human(Path("test.py"), resp, classify=True)
        assert "decision: marginal" in output
        assert "decision: warn" not in output


class TestFormatResultsJson:
    def test_valid_json_matching_schema(self):
        from eigenhelm.helm import DynamicHelm, EvaluationRequest

        helm = DynamicHelm()
        resp = helm.evaluate(
            EvaluationRequest(source="def f(): pass", language="python")
        )
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


class TestEvaluateThresholdPrecedence:
    def test_cli_thresholds_override_config(self, tmp_path, monkeypatch):
        from eigenhelm.cli.evaluate import main
        from eigenhelm.config import ProjectConfig, ThresholdConfig
        from eigenhelm.helm import EvaluationRequest, EvaluationResponse

        # Fake a config that specifies an accept threshold of 0.99
        fake_config = ProjectConfig(
            model=None,
            strict=False,
            language=None,
            exclude=(),
            language_overrides={},
            thresholds=ThresholdConfig(accept=0.99, reject=None),
        )

        # Mock config loading
        def mock_load():
            return fake_config, tmp_path / ".eigenhelm.toml"

        monkeypatch.setattr("eigenhelm.cli.evaluate._load_project_config", mock_load)

        # Create a mock file
        f = tmp_path / "sample.py"
        f.write_text("x = 1")

        # We want to assert that the CLI flag threshold is used, not 0.99.
        # If CLI flag is 0.0, and the file gets a score of e.g. 0.62,
        # it is > 0.0, so it shouldn't be accepted by the CLI threshold.
        # But if the 0.99 config threshold wins, it WILL be accepted.

        # Let's mock DynamicHelm to always return score 0.62 and initial decision "reject"
        # Since 0.62 > reject_threshold (0.0001).

        class MockHelm:
            def __init__(self, *args, **kwargs):
                pass

            def evaluate(self, req: EvaluationRequest):
                return EvaluationResponse(
                    decision="reject",
                    score=0.62,
                    structural_confidence="high",
                    critique=None,
                )

        monkeypatch.setattr("eigenhelm.cli.evaluate.DynamicHelm", MockHelm)

        # Run main with CLI threshold
        args = ["--accept-threshold", "0.0", "--reject-threshold", "0.0001", str(f)]

        # Capture output or check exit code
        # Exit code: 0 (accept), 1 (warn), 2 (reject), 3 (error)
        # If CLI wins, it should exit with 2 (reject) because score 0.62 > 0.0001
        # If config wins, it would exit with 0 (accept) because score 0.62 < 0.99
        exit_code = main(args)
        assert exit_code == 2, "CLI thresholds should override config file thresholds"

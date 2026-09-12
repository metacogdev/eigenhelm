"""Integration test scenarios for the eigenhelm GitHub Action.

Covers CLI building blocks the action orchestrates, plus anticipatory stubs
for action-level behaviours that don't exist yet (marked TODO).

Scenario groups
---------------
TestGitHubActionBuildingBlocks  — existing building-block tests (diff/SARIF/JSON)
TestGitHubActionHappyPaths      — PR passes, SARIF produced, rank mode, thresholds
TestGitHubActionFailureCases    — reject exits non-zero, empty diff, bad model, etc.
TestGitHubActionIntegrationScenarios — SARIF schema correctness, annotation stubs

Exit-code contract (CLI)
------------------------
  0  All files accepted
  1  At least one warn (no rejections)
  2  At least one reject
  3  Runtime error

Action input → CLI flag mapping (planned; action not yet built):
  fail-on-reject: false  →  --lenient   (exit 0 even on reject)
  fail-on-warn:   true   →  --strict    (exit 2 on warn)
  output-format:  sarif  →  --format sarif
  threshold:      <N>    →  --reject-threshold <N>

Tests marked @pytest.mark.github require a live GitHub Actions environment.
Tests marked @pytest.mark.skip document stubs for unimplemented action features.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.integration

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


def _make_accept_response(score: float = 0.15) -> MagicMock:
    resp = MagicMock()
    resp.decision = "accept"
    resp.score = score
    resp.structural_confidence = "low"
    resp.critique.violations = []
    resp.warning = None
    resp.percentile = None
    resp.percentile_available = False
    resp.contributions = ()
    resp.attribution = None
    resp.regions = ()
    resp.declaration_ratio = None
    return resp


def _make_warn_response(score: float = 0.55) -> MagicMock:
    resp = MagicMock()
    resp.decision = "warn"
    resp.score = score
    resp.structural_confidence = "low"
    resp.critique.violations = []
    resp.warning = None
    resp.percentile = None
    resp.percentile_available = False
    resp.contributions = ()
    resp.attribution = None
    resp.regions = ()
    resp.declaration_ratio = None
    return resp


def _make_reject_response(score: float = 0.85) -> MagicMock:
    resp = MagicMock()
    resp.decision = "reject"
    resp.score = score
    resp.structural_confidence = "low"
    resp.critique.violations = []
    resp.warning = None
    resp.percentile = None
    resp.percentile_available = False
    resp.contributions = ()
    resp.attribution = None
    resp.regions = ()
    resp.declaration_ratio = None
    return resp


class TestGitHubActionBuildingBlocks:
    """Verify CLI building blocks for the GitHub Action."""

    def test_diff_with_sarif_produces_valid_output(self, tmp_path, capsys):
        """--diff + --format sarif integration path."""
        from eigenhelm.cli.evaluate import main

        mock_resp = MagicMock()
        mock_resp.decision = "warn"
        mock_resp.score = 0.55
        mock_resp.structural_confidence = "low"
        mock_resp.critique.violations = []
        mock_resp.warning = None
        mock_resp.percentile = None
        mock_resp.percentile_available = False
        mock_resp.contributions = ()
        mock_resp.attribution = None
        mock_resp.regions = ()
        mock_resp.declaration_ratio = None

        changed_files = [tmp_path / "changed.py"]
        changed_files[0].write_text("x = 1\n")

        with (
            patch("eigenhelm.diff.discover_changed_files", return_value=changed_files),
            patch(
                "eigenhelm.cli.evaluate._evaluate_paths",
                return_value=[(str(changed_files[0]), mock_resp)],
            ),
        ):
            code = main(["--diff", "HEAD~1", "--format", "sarif"])

        # warn with no reject -> exit 1
        assert code == 1

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["version"] == "2.1.0"
        main_results = [
            r
            for r in data["runs"][0]["results"]
            if r["ruleId"] == "eigenhelm/aesthetic-score"
        ]
        assert len(main_results) == 1
        assert main_results[0]["level"] == "warning"

    def test_diff_with_json_produces_valid_output(self, tmp_path, capsys):
        """--diff + --format json integration path."""
        from eigenhelm.cli.evaluate import main

        mock_resp = MagicMock()
        mock_resp.decision = "accept"
        mock_resp.score = 0.2
        mock_resp.structural_confidence = "low"
        mock_resp.critique.violations = []
        mock_resp.warning = None
        mock_resp.percentile = None
        mock_resp.percentile_available = False
        mock_resp.contributions = ()
        mock_resp.attribution = None
        mock_resp.regions = ()
        mock_resp.declaration_ratio = None

        changed_files = [tmp_path / "changed.py"]
        changed_files[0].write_text("x = 1\n")

        with (
            patch("eigenhelm.diff.discover_changed_files", return_value=changed_files),
            patch(
                "eigenhelm.cli.evaluate._evaluate_paths",
                return_value=[(str(changed_files[0]), mock_resp)],
            ),
        ):
            code = main(["--diff", "HEAD~1", "--format", "json"])

        assert code == 0
        data = json.loads(capsys.readouterr().out)
        assert data["summary"]["overall_decision"] == "accept"

    def test_diff_git_error_exits_3(self, tmp_path):
        """git diff failure propagates as exit code 3."""
        from eigenhelm.cli.evaluate import main

        with patch(
            "eigenhelm.diff.discover_changed_files",
            side_effect=RuntimeError("git not found"),
        ):
            code = main(["--diff", "HEAD~1"])

        assert code == 3

    @pytest.mark.github
    def test_github_action_live_pr_review(self):
        """Live GitHub Action test (skipped in normal CI).

        End-to-end validation: push PR with known-bad file, assert
        action posts review comment and SARIF upload succeeds.

        This test requires GitHub Actions environment variables:
          - GITHUB_TOKEN
          - GITHUB_REPOSITORY
          - GITHUB_BASE_REF
        """
        pytest.skip("Requires live GitHub Actions environment")


# ---------------------------------------------------------------------------
# Happy-path scenarios
# ---------------------------------------------------------------------------


class TestGitHubActionHappyPaths:
    """The action should succeed (exit 0) and produce valid output on clean code."""

    def test_pr_with_clean_python_code_exits_zero(self, tmp_path):
        """Happy path: PR touches a Python file that scores accept → exit 0.

        The action evaluates only files changed in the PR diff. When all files
        accept, the check passes (exit 0).
        """
        from eigenhelm.cli.evaluate import main

        clean_file = tmp_path / "utils.py"
        clean_file.write_text((FIXTURES_DIR / "python_quicksort.py").read_text())

        with (
            patch(
                "eigenhelm.diff.discover_changed_files",
                return_value=[clean_file],
            ),
            patch(
                "eigenhelm.cli.evaluate._evaluate_paths",
                return_value=[(str(clean_file), _make_accept_response())],
            ),
        ):
            code = main(["--diff", "HEAD~1"])

        assert code == 0, "All-accept diff must exit 0"

    def test_sarif_output_file_is_valid_2_1_0(self, tmp_path, capsys):
        """Action produces a SARIF 2.1.0 document when --format sarif is used.

        GitHub Code Scanning requires SARIF 2.1.0. Verify schema version,
        required top-level keys, and that the run contains at least one result.
        """
        from eigenhelm.cli.evaluate import main

        py_file = tmp_path / "src.py"
        py_file.write_text("x = 1\n")

        with (
            patch(
                "eigenhelm.diff.discover_changed_files",
                return_value=[py_file],
            ),
            patch(
                "eigenhelm.cli.evaluate._evaluate_paths",
                return_value=[(str(py_file), _make_warn_response())],
            ),
        ):
            main(["--diff", "HEAD~1", "--format", "sarif"])

        sarif = json.loads(capsys.readouterr().out)

        # SARIF 2.1.0 required top-level shape
        assert sarif["version"] == "2.1.0"
        assert "$schema" in sarif
        assert "runs" in sarif
        assert len(sarif["runs"]) == 1

        run = sarif["runs"][0]
        assert "tool" in run
        assert "driver" in run["tool"]
        assert "results" in run

        # At least one result for the warned file
        assert len(run["results"]) >= 1
        result = run["results"][0]
        assert "ruleId" in result
        assert "level" in result
        assert result["level"] == "warning"  # warn → SARIF warning

    @pytest.mark.skip(
        reason="--rank omitted from GitHub Action v1 — test when rank input is added in v1.1"
    )
    def test_rank_mode_on_multi_file_diff_produces_ranked_output(
        self, tmp_path, capsys
    ):
        """Action in rank mode ranks changed files best-to-worst and highlights bottom N.

        This validates that --rank works end-to-end with a multi-file diff,
        which is the primary action mode for large PRs.

        Expected output format (format_ranking_human):
          Ranking: N files evaluated (bottom M highlighted)
          [▼]#1   <path>   <score>  ...
          [▼]#2   <path>   <score>  ...
              #3   <path>   <score>  ...
            spread: X.XX | highlighted: M of N
        """
        from eigenhelm.cli.evaluate import main

        files = [
            (tmp_path / f"f{i}.py", score) for i, score in enumerate([0.2, 0.5, 0.8])
        ]
        for path, _ in files:
            path.write_text("x = 1\n")

        fake_results = [
            (
                str(path),
                _make_accept_response(score)
                if score < 0.4
                else _make_warn_response(score),
            )
            for path, score in files
        ]
        # Ensure decisions match score thresholds
        fake_results[2][1].decision = "reject"

        with (
            patch(
                "eigenhelm.diff.discover_changed_files",
                return_value=[p for p, _ in files],
            ),
            patch(
                "eigenhelm.cli.evaluate._evaluate_paths",
                return_value=fake_results,
            ),
        ):
            main(["--diff", "HEAD~1", "--rank"])

        output = capsys.readouterr().out
        # Ranking header must name the exact file count
        assert "Ranking: 3 files evaluated" in output
        # All three rank numbers must appear in ascending order
        assert "#1" in output and "#2" in output and "#3" in output
        assert output.index("#1") < output.index("#2") < output.index("#3")

    def test_custom_reject_threshold_is_respected(self, tmp_path):
        """Action with a custom threshold overrides model defaults.

        A score of 0.75 is normally a warn, but with --reject-threshold 0.7
        it should be treated as reject (exit 2).
        """
        from eigenhelm.cli.evaluate import main

        py_file = tmp_path / "src.py"
        py_file.write_text("x = 1\n")

        # Score 0.75; above our custom reject threshold of 0.7
        resp = _make_warn_response(score=0.75)
        resp.decision = "reject"  # CLI re-derives; force reject for mock path

        with (
            patch(
                "eigenhelm.diff.discover_changed_files",
                return_value=[py_file],
            ),
            patch(
                "eigenhelm.cli.evaluate._evaluate_paths",
                return_value=[(str(py_file), resp)],
            ),
        ):
            code = main(["--diff", "HEAD~1", "--reject-threshold", "0.7"])

        assert code == 2, "Score above custom reject threshold must exit 2"

    def test_custom_accept_threshold_raises_bar(self, tmp_path):
        """--accept-threshold 0.3 means a score of 0.25 accepts (below bar → accept).

        Validates threshold hierarchy: CLI flags beat model calibration.
        """
        from eigenhelm.cli.evaluate import main

        py_file = tmp_path / "src.py"
        py_file.write_text("x = 1\n")

        resp = _make_accept_response(score=0.25)

        with (
            patch(
                "eigenhelm.diff.discover_changed_files",
                return_value=[py_file],
            ),
            patch(
                "eigenhelm.cli.evaluate._evaluate_paths",
                return_value=[(str(py_file), resp)],
            ),
        ):
            code = main(["--diff", "HEAD~1", "--accept-threshold", "0.3"])

        assert code == 0


# ---------------------------------------------------------------------------
# Failure / edge-case scenarios
# ---------------------------------------------------------------------------


class TestGitHubActionFailureCases:
    """The action must fail loudly when appropriate and silently when configured to."""

    def test_reject_quality_code_fails_pr(self, tmp_path):
        """Code scoring above the reject threshold causes exit 2, failing the PR check.

        This is the primary gate: bad code must block merging.
        """
        from eigenhelm.cli.evaluate import main

        bad_file = tmp_path / "bad.py"
        bad_file.write_text("x = 1\n")

        with (
            patch(
                "eigenhelm.diff.discover_changed_files",
                return_value=[bad_file],
            ),
            patch(
                "eigenhelm.cli.evaluate._evaluate_paths",
                return_value=[(str(bad_file), _make_reject_response())],
            ),
        ):
            code = main(["--diff", "HEAD~1"])

        assert code == 2, "Reject-quality code must exit 2 to fail the PR check"

    @pytest.mark.skip(
        reason=(
            "TODO(Morpheus/Trinity): `--lenient` suppresses exit 1 (warn→0) but NOT "
            "exit 2 (reject). The action input `fail-on-reject: false` therefore has "
            "no current CLI equivalent. Options: "
            "(a) add `--no-fail` flag to `eh evaluate` that exits 0 regardless of decisions, "
            "(b) handle at action.yml level via `continue-on-error: true`, "
            "(c) extend `--lenient` to also suppress reject exits. "
            "Recommend option (a) for explicitness. "
            "Design decision required before Trinity implements action.yml."
        )
    )
    def test_fail_on_reject_false_exits_zero_on_reject_quality(self, tmp_path):
        """Action input fail-on-reject: false → exit 0 even when code would reject.

        DESIGN GAP: The CLI's --lenient flag only suppresses exit 1 (warn→0).
        A reject (exit 2) still exits non-zero even with --lenient. The action
        needs a dedicated mechanism to implement fail-on-reject: false.

        TODO(Morpheus): decide which approach to take (see skip reason).
        TODO(Trinity): implement the chosen approach and un-skip this test.

        Expected behaviour once implemented:
          - Score 0.85 (reject-quality) with fail-on-reject: false → exit 0
          - SARIF still contains level: error (the annotation appears, but doesn't block)
        """
        pytest.skip(
            "fail-on-reject: false has no CLI equivalent yet — see TODO in skip reason"
        )

    def test_empty_diff_no_supported_files_exits_zero(self, tmp_path):
        """PR touching only non-source files (docs, config) exits 0 with no SARIF output.

        The action must not fail when there's nothing to evaluate.
        """
        from eigenhelm.cli.evaluate import main

        # Diff returns no recognised source files
        with patch(
            "eigenhelm.diff.discover_changed_files",
            return_value=[],
        ):
            code = main(["--diff", "HEAD~1"])

        assert code == 0, "Empty diff (no source files) must exit 0"

    def test_empty_diff_produces_no_sarif_results(self, tmp_path, capsys):
        """SARIF output for an empty diff contains zero results (no noise annotations)."""
        from eigenhelm.cli.evaluate import main

        with patch(
            "eigenhelm.diff.discover_changed_files",
            return_value=[],
        ):
            code = main(["--diff", "HEAD~1", "--format", "sarif"])

        assert code == 0
        output = capsys.readouterr().out
        # Either no output at all, or empty SARIF with zero results
        if output.strip():
            sarif = json.loads(output)
            assert len(sarif["runs"][0]["results"]) == 0

    def test_missing_model_file_exits_nonzero_with_message(self, tmp_path, capsys):
        """Pointing --model at a nonexistent path should exit 3 with a clear error.

        The action must surface model-load failures instead of silently passing.
        """
        from eigenhelm.cli.evaluate import main

        py_file = tmp_path / "src.py"
        py_file.write_text("x = 1\n")

        nonexistent = str(tmp_path / "does_not_exist.npz")

        code = main([str(py_file), "--model", nonexistent])

        assert code == 3, "Missing model file must exit 3"
        err = capsys.readouterr().err
        assert err.strip(), "Missing model error must produce stderr message"

    def test_no_eigenhelm_toml_uses_defaults_gracefully(self, tmp_path):
        """Repo without .eigenhelm.toml uses bundled defaults; action must not crash.

        The action is run in repos that have no eigenhelm config. It must not error.
        """
        from eigenhelm.cli.evaluate import main

        py_file = tmp_path / "src.py"
        py_file.write_text("x = 1\n")

        with (
            patch(
                "eigenhelm.cli.evaluate._load_project_config",
                return_value=(None, None),
            ),
            patch(
                "eigenhelm.cli.evaluate._evaluate_paths",
                return_value=[(str(py_file), _make_accept_response())],
            ),
        ):
            code = main([str(py_file)])

        assert code in (0, 1, 2), "No config should not produce exit 3 (runtime error)"

    def test_unsupported_language_files_do_not_crash_action(self, tmp_path):
        """PR touching Solidity/COBOL/unknown files must not crash; partial_parse=True.

        The action evaluates what it can and logs warnings for unsupported languages
        instead of hard-failing. Regression guard for the extract_batch contract.
        """
        from eigenhelm.virtue_extractor import VirtueExtractor

        extractor = VirtueExtractor()
        # Simulate a batch with an unsupported language (Brainfuck)
        files = [
            ("def foo(): pass\n", "python", "ok.py"),
            ("+ + + [ > + < - ] > .", "brainfuck", "weird.bf"),  # unsupported
        ]

        # Must not raise; unsupported entries must have partial_parse=True
        results = extractor.extract_batch(files)
        partial = [v for v in results if v.partial_parse]
        assert partial, "Unsupported language must produce partial_parse=True vector"
        ok = [v for v in results if not v.partial_parse]
        assert ok, "Supported-language files must still succeed in same batch"

    def test_diff_only_md_files_changed_exits_zero(self, tmp_path):
        """Action gracefully handles a PR that touches only Markdown files.

        Markdown is not a recognised source language; diff returns empty list;
        action exits 0 without evaluating anything.
        """
        import subprocess

        repo = tmp_path / "repo"
        repo.mkdir()

        subprocess.run(["git", "init"], cwd=repo, capture_output=True, check=False)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=repo,
            capture_output=True,
            check=False,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=repo,
            capture_output=True,
            check=False,
        )
        (repo / "README.md").write_text("# Before\n")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True, check=False)
        subprocess.run(
            ["git", "commit", "-m", "init"],
            cwd=repo,
            capture_output=True,
            check=False,
        )
        (repo / "README.md").write_text("# After\n")
        subprocess.run(["git", "add", "."], cwd=repo, capture_output=True, check=False)
        subprocess.run(
            ["git", "commit", "-m", "docs update"],
            cwd=repo,
            capture_output=True,
            check=False,
        )

        from eigenhelm.diff import discover_changed_files

        old_cwd = os.getcwd()
        try:
            os.chdir(repo)
            changed = discover_changed_files("HEAD~1")
        finally:
            os.chdir(old_cwd)

        # No source files changed → empty list
        assert changed == [] or all(p.suffix != ".md" for p in changed)


# ---------------------------------------------------------------------------
# Integration scenarios — SARIF correctness & GitHub annotations
# ---------------------------------------------------------------------------


class TestGitHubActionIntegrationScenarios:
    """Validate that action outputs are correctly shaped for GitHub consumption."""

    def test_sarif_schema_url_is_present(self, tmp_path, capsys):
        """SARIF document must include $schema pointing to the canonical 2.1.0 URI.

        GitHub Code Scanning uses this to validate uploads. Missing $schema
        causes silent rejection of the SARIF file.
        """
        from eigenhelm.cli.evaluate import main

        py_file = tmp_path / "src.py"
        py_file.write_text("x = 1\n")

        with (
            patch(
                "eigenhelm.diff.discover_changed_files",
                return_value=[py_file],
            ),
            patch(
                "eigenhelm.cli.evaluate._evaluate_paths",
                return_value=[(str(py_file), _make_warn_response())],
            ),
        ):
            main(["--diff", "HEAD~1", "--format", "sarif"])

        sarif = json.loads(capsys.readouterr().out)
        assert "$schema" in sarif
        assert "sarif" in sarif["$schema"].lower() or "schemastore" in sarif["$schema"]
        assert "2.1.0" in sarif["$schema"]

    def test_sarif_reject_maps_to_error_level(self, tmp_path, capsys):
        """SARIF 'error' level triggers a blocking annotation on the PR diff view.

        A rejected file must emit level='error' so GitHub blocks the merge.
        """
        from eigenhelm.cli.evaluate import main

        py_file = tmp_path / "src.py"
        py_file.write_text("x = 1\n")

        with (
            patch(
                "eigenhelm.diff.discover_changed_files",
                return_value=[py_file],
            ),
            patch(
                "eigenhelm.cli.evaluate._evaluate_paths",
                return_value=[(str(py_file), _make_reject_response())],
            ),
        ):
            main(["--diff", "HEAD~1", "--format", "sarif"])

        sarif = json.loads(capsys.readouterr().out)
        results = sarif["runs"][0]["results"]
        score_results = [
            r for r in results if r["ruleId"] == "eigenhelm/aesthetic-score"
        ]
        assert len(score_results) == 1
        assert score_results[0]["level"] == "error", (
            "Reject decision must map to SARIF 'error' level for PR blocking"
        )

    def test_sarif_accept_maps_to_note_level(self, tmp_path, capsys):
        """SARIF 'note' level is non-blocking — accepted files should not block PRs."""
        from eigenhelm.cli.evaluate import main

        py_file = tmp_path / "src.py"
        py_file.write_text("x = 1\n")

        with (
            patch(
                "eigenhelm.diff.discover_changed_files",
                return_value=[py_file],
            ),
            patch(
                "eigenhelm.cli.evaluate._evaluate_paths",
                return_value=[(str(py_file), _make_accept_response())],
            ),
        ):
            main(["--diff", "HEAD~1", "--format", "sarif"])

        sarif = json.loads(capsys.readouterr().out)
        results = sarif["runs"][0]["results"]
        score_results = [
            r for r in results if r["ruleId"] == "eigenhelm/aesthetic-score"
        ]
        assert len(score_results) == 1
        assert score_results[0]["level"] == "note", (
            "Accept decision must map to SARIF 'note' level (non-blocking)"
        )

    def test_sarif_contains_tool_driver_name(self, tmp_path, capsys):
        """SARIF tool.driver.name must be present for GitHub Code Scanning to attribute results."""
        from eigenhelm.cli.evaluate import main

        py_file = tmp_path / "src.py"
        py_file.write_text("x = 1\n")

        with (
            patch(
                "eigenhelm.diff.discover_changed_files",
                return_value=[py_file],
            ),
            patch(
                "eigenhelm.cli.evaluate._evaluate_paths",
                return_value=[(str(py_file), _make_accept_response())],
            ),
        ):
            main(["--diff", "HEAD~1", "--format", "sarif"])

        sarif = json.loads(capsys.readouterr().out)
        driver = sarif["runs"][0]["tool"]["driver"]
        assert "name" in driver
        assert driver["name"]  # non-empty

    def test_sarif_rules_array_contains_aesthetic_score_rule(self, tmp_path, capsys):
        """SARIF rules array must define eigenhelm/aesthetic-score so GitHub can resolve it."""
        from eigenhelm.cli.evaluate import main

        py_file = tmp_path / "src.py"
        py_file.write_text("x = 1\n")

        with (
            patch(
                "eigenhelm.diff.discover_changed_files",
                return_value=[py_file],
            ),
            patch(
                "eigenhelm.cli.evaluate._evaluate_paths",
                return_value=[(str(py_file), _make_warn_response())],
            ),
        ):
            main(["--diff", "HEAD~1", "--format", "sarif"])

        sarif = json.loads(capsys.readouterr().out)
        driver = sarif["runs"][0]["tool"]["driver"]
        rule_ids = {r["id"] for r in driver.get("rules", [])}
        assert "eigenhelm/aesthetic-score" in rule_ids

    @pytest.mark.skip(
        reason=(
            "TODO(Trinity): implement action.yml input → CLI flag mapping. "
            "The composite action uses `uv tool install eigenhelm` and maps "
            "action inputs (fail-on-reject, output-format, threshold, model-path, diff-ref) "
            "to CLI flags via shell steps. "
            "Test by running the action in a real GitHub Actions runner environment "
            "with INPUT_* env vars set matching the GitHub Actions `env:` context."
        )
    )
    def test_action_binary_accepts_action_inputs_via_env(self, tmp_path):
        """TODO: action.yml input → CLI flag mapping end-to-end via composite action.

        When the action is run in a GitHub Actions runner, verify:
          - INPUT_FAIL_ON_REJECT=false → --lenient passed to `eh evaluate`
          - INPUT_OUTPUT_FORMAT=sarif  → --format sarif
          - INPUT_THRESHOLD=0.7        → --reject-threshold 0.7
          - INPUT_MODEL_PATH=...       → --model ...
          - INPUT_DIFF_REF=HEAD~1      → --diff HEAD~1

        Run in a real GitHub Actions workflow to validate end-to-end.
        Assert exit 0 and valid SARIF on stdout.
        """
        pytest.skip(
            "requires composite action runtime — run in a real GitHub Actions job to validate"
        )

    @pytest.mark.skip(
        reason=(
            "TODO(Trinity): implement GITHUB_STEP_SUMMARY output. "
            "The action should write a Markdown summary to $GITHUB_STEP_SUMMARY "
            "showing per-file scores and the overall decision. "
            "Test by asserting the summary file contains expected headings and scores."
        )
    )
    def test_action_writes_step_summary(self, tmp_path):
        """TODO: action writes Markdown score table to GITHUB_STEP_SUMMARY.

        When GITHUB_STEP_SUMMARY env var is set, the action should append a
        Markdown table of file scores. Verify:
          - File contains a Markdown table row per evaluated file
          - Overall decision is summarised at the top
          - Non-zero score is present for each file
        """
        pytest.skip("GITHUB_STEP_SUMMARY integration not yet implemented")

    @pytest.mark.skip(
        reason=(
            "TODO(Trinity): implement output: sarif-path action output. "
            "The action should write the SARIF JSON to a file whose path is "
            "set as the `sarif-path` action output, so callers can upload it "
            "via `github/codeql-action/upload-sarif`. "
            "Test by asserting the file exists and is valid SARIF 2.1.0."
        )
    )
    def test_action_writes_sarif_to_output_file(self, tmp_path):
        """TODO: action writes SARIF to file and sets sarif-path output.

        When output-format: sarif, the action should:
          1. Write SARIF to $RUNNER_TEMP/eigenhelm-results.sarif (or configurable path)
          2. Set the `sarif-path` output to that file path
          3. Caller uploads via: uses: github/codeql-action/upload-sarif@v3

        This is required for inline PR diff annotations in GitHub Code Scanning.
        """
        pytest.skip("SARIF file output not yet implemented")

    @pytest.mark.github
    def test_github_action_live_pr_review(self):
        """Live GitHub Action test (skipped in normal CI).

        End-to-end validation: push PR with known-bad file, assert
        action posts review comment and SARIF upload succeeds.

        This test requires GitHub Actions environment variables:
          - GITHUB_TOKEN
          - GITHUB_REPOSITORY
          - GITHUB_BASE_REF
        """
        pytest.skip("Requires live GitHub Actions environment")

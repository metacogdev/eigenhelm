"""Integration test scaffold for GitHub Action workflow.

These tests validate that the CLI building blocks needed by the eigenhelm
GitHub Action work correctly together:
  - --diff <range> discovers changed files
  - --format sarif produces valid SARIF
  - --format json produces valid JSON
  - exit codes are correct

Tests marked @pytest.mark.github are skipped in normal CI (require live
GitHub Actions environment). Other tests run in CI.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.integration


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

        changed_files = [tmp_path / "changed.py"]
        changed_files[0].write_text("x = 1\n")

        with (
            patch("eigenhelm.diff.discover_changed_files", return_value=changed_files),
            patch("eigenhelm.cli.evaluate._evaluate_paths", return_value=[(str(changed_files[0]), mock_resp)]),
        ):
            code = main(["--diff", "HEAD~1", "--format", "sarif"])

        # warn with no reject -> exit 1
        assert code == 1

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["version"] == "2.1.0"
        main_results = [r for r in data["runs"][0]["results"] if r["ruleId"] == "eigenhelm/aesthetic-score"]
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

        changed_files = [tmp_path / "changed.py"]
        changed_files[0].write_text("x = 1\n")

        with (
            patch("eigenhelm.diff.discover_changed_files", return_value=changed_files),
            patch("eigenhelm.cli.evaluate._evaluate_paths", return_value=[(str(changed_files[0]), mock_resp)]),
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

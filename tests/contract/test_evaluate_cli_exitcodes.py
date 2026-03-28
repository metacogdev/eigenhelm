"""Contract tests for eigenhelm-evaluate CLI exit codes."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from eigenhelm.cli.evaluate import main

pytestmark = pytest.mark.contract


def _run_with_results(decisions: list[str], extra_args: list[str] | None = None) -> int:
    """Helper: run main() with mocked evaluation results and return exit code."""
    mock_responses = []
    for decision in decisions:
        resp = MagicMock()
        resp.decision = decision
        resp.score = 0.5
        resp.structural_confidence = "low"
        resp.critique.violations = []
        resp.warning = None
        mock_responses.append(resp)

    results = [(f"file{i}.py", r) for i, r in enumerate(mock_responses)]

    with patch("eigenhelm.cli.evaluate._evaluate_paths", return_value=results):
        args = [str(Path(__file__))]  # Dummy path argument
        if extra_args:
            args += extra_args
        return main(args)


class TestExitCodesContract:
    def test_all_accept_exit_0(self):
        code = _run_with_results(["accept", "accept"])
        assert code == 0

    def test_warn_only_exit_1(self):
        code = _run_with_results(["warn", "accept"])
        assert code == 1

    def test_reject_exit_2(self):
        code = _run_with_results(["reject"])
        assert code == 2

    def test_mixed_warn_reject_exit_2(self):
        code = _run_with_results(["warn", "reject"])
        assert code == 2

    def test_strict_warn_exit_2(self):
        code = _run_with_results(["warn"], extra_args=["--strict"])
        assert code == 2

    def test_lenient_warn_exit_0(self):
        code = _run_with_results(["warn"], extra_args=["--lenient"])
        assert code == 0

    def test_runtime_error_exits_3(self, tmp_path):
        # No language with stdin mode = error 3
        with patch(
            "eigenhelm.cli.evaluate._evaluate_paths", side_effect=Exception("boom")
        ):
            code = main([str(tmp_path / "file.py")])
        assert code == 3

    def test_strict_and_lenient_mutually_exclusive(self, tmp_path):
        """argparse should reject --strict --lenient together."""
        with pytest.raises(SystemExit):
            main([str(tmp_path), "--strict", "--lenient"])

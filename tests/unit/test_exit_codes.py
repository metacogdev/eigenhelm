"""Unit tests for exit code computation logic."""

from __future__ import annotations

from unittest.mock import MagicMock


from eigenhelm.cli.evaluate import compute_exit_code


def _make_result(decision: str):
    """Create a mock (path, EvaluationResponse) tuple."""
    resp = MagicMock()
    resp.decision = decision
    return ("file.py", resp)


class TestComputeExitCode:
    def test_all_accept_returns_0(self):
        results = [_make_result("accept"), _make_result("accept")]
        assert compute_exit_code(results) == 0

    def test_empty_results_returns_0(self):
        assert compute_exit_code([]) == 0

    def test_warn_only_returns_1(self):
        results = [_make_result("warn"), _make_result("accept")]
        assert compute_exit_code(results) == 1

    def test_reject_only_returns_2(self):
        results = [_make_result("reject")]
        assert compute_exit_code(results) == 2

    def test_mixed_warn_and_reject_returns_2(self):
        results = [_make_result("warn"), _make_result("reject"), _make_result("accept")]
        assert compute_exit_code(results) == 2

    def test_strict_warn_becomes_reject(self):
        results = [_make_result("warn")]
        assert compute_exit_code(results, strict=True) == 2

    def test_strict_accept_stays_0(self):
        results = [_make_result("accept")]
        assert compute_exit_code(results, strict=True) == 0

    def test_lenient_warn_becomes_accept(self):
        results = [_make_result("warn")]
        assert compute_exit_code(results, lenient=True) == 0

    def test_lenient_reject_still_2(self):
        results = [_make_result("reject")]
        assert compute_exit_code(results, lenient=True) == 2

    def test_lenient_mixed_warn_reject_returns_2(self):
        results = [_make_result("warn"), _make_result("reject")]
        assert compute_exit_code(results, lenient=True) == 2

    def test_strict_and_lenient_mutual_exclusion(self):
        """strict=True takes precedence over lenient=True when both are passed."""
        results = [_make_result("warn")]
        # strict takes precedence: warn should be treated as reject (exit 2)
        assert compute_exit_code(results, strict=True, lenient=True) == 2

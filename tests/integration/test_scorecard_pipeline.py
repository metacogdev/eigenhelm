"""Integration tests for scorecard pipeline (T040)."""

from __future__ import annotations

import json

import pytest
from eigenhelm.cli.evaluate import main

pytestmark = pytest.mark.integration


class TestScorecardCLI:
    """Tests for --scorecard CLI flag."""

    def test_scorecard_human_output(self, tmp_path) -> None:
        """--scorecard produces human-readable scorecard."""
        sample = tmp_path / "sample.py"
        sample.write_text("def foo():\n    return 42\n")
        # Run with capsys indirectly via return code
        exit_code = main([str(sample), "--scorecard"])
        assert exit_code in (0, 1, 2)

    def test_scorecard_json_output(self, tmp_path, capsys) -> None:
        """--scorecard --json produces valid JSON."""
        sample = tmp_path / "sample.py"
        sample.write_text("def foo():\n    return 42\n")
        exit_code = main([str(sample), "--scorecard", "--json"])
        captured = capsys.readouterr()
        parsed = json.loads(captured.out)
        assert "entries" in parsed
        assert "summary" in parsed
        assert exit_code in (0, 1, 2)

    def test_scorecard_covers_all_files(self, tmp_path, capsys) -> None:
        """Scorecard includes all evaluated files."""
        for i in range(3):
            f = tmp_path / f"file{i}.py"
            f.write_text(f"def f{i}():\n    return {i}\n")
        main([str(tmp_path), "--scorecard", "--json"])
        captured = capsys.readouterr()
        parsed = json.loads(captured.out)
        assert len(parsed["entries"]) == 3
        assert parsed["summary"]["total_files"] == 3

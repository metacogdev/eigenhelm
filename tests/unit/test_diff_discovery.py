"""Unit tests for diff-aware file discovery."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from eigenhelm.diff import discover_changed_files


def _mock_run(stdout: str, returncode: int = 0):
    """Helper: create a mock subprocess result."""
    result = MagicMock()
    result.returncode = returncode
    result.stdout = stdout
    result.stderr = ""
    return result


class TestDiscoverChangedFiles:
    def test_valid_output_returns_paths(self):
        with patch(
            "subprocess.run", return_value=_mock_run("src/foo.py\nsrc/bar.py\n")
        ):
            paths = discover_changed_files("HEAD~1")
        assert Path("src/foo.py") in paths
        assert Path("src/bar.py") in paths

    def test_empty_diff_returns_empty_list(self):
        with patch("subprocess.run", return_value=_mock_run("")):
            paths = discover_changed_files("HEAD~1")
        assert paths == []

    def test_filters_unrecognized_extensions(self):
        with patch(
            "subprocess.run",
            return_value=_mock_run("src/code.py\nREADME.md\nconfig.yaml\nscript.sh\n"),
        ):
            paths = discover_changed_files("HEAD~1")
        assert Path("src/code.py") in paths
        assert all(
            p.suffix in {".py"} or p.suffix in {".js", ".ts", ".go", ".rs", ".java"}
            for p in paths
        )
        assert Path("README.md") not in paths

    def test_git_not_found_raises_runtime_error(self):
        with patch("subprocess.run", side_effect=FileNotFoundError("git not found")):
            with pytest.raises(RuntimeError, match="git not found"):
                discover_changed_files("HEAD~1")

    def test_invalid_revision_raises_runtime_error(self):
        with patch(
            "subprocess.run",
            return_value=_mock_run("", returncode=128),
        ) as mock_run:
            mock_run.return_value.stderr = "fatal: ambiguous argument 'badrev'"
            with pytest.raises(RuntimeError, match="git diff failed"):
                discover_changed_files("badrev")

    def test_uses_correct_git_command(self):
        with patch("subprocess.run", return_value=_mock_run("")) as mock_run:
            discover_changed_files("HEAD~2")
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == "git"
        assert "--diff-filter=ACMR" in call_args
        assert "HEAD~2" in call_args

    def test_skips_blank_lines(self):
        with patch(
            "subprocess.run", return_value=_mock_run("\nsrc/foo.py\n\nsrc/bar.py\n")
        ):
            paths = discover_changed_files("HEAD~1")
        assert len([p for p in paths if p.suffix == ".py"]) == 2

    def test_returns_path_objects(self):
        with patch("subprocess.run", return_value=_mock_run("src/module.py\n")):
            paths = discover_changed_files("HEAD~1")
        assert all(isinstance(p, Path) for p in paths)

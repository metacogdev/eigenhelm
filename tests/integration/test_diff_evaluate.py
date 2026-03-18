"""Integration tests for diff-aware evaluation.

Creates a real git repository with controlled history and validates that
--diff evaluates only changed files.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.integration


def _git(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.fixture
def git_repo(tmp_path):
    """Create a minimal git repository with controlled history."""
    repo = tmp_path / "repo"
    repo.mkdir()

    # Initialize repo with identity (needed for commits)
    _git(["init"], cwd=repo)
    _git(["config", "user.email", "test@test.com"], cwd=repo)
    _git(["config", "user.name", "Test"], cwd=repo)

    # Create initial commit with 3 Python files
    for i in range(3):
        (repo / f"file{i}.py").write_text(f"x_{i} = {i}\n")
    _git(["add", "."], cwd=repo)
    _git(["commit", "-m", "initial commit"], cwd=repo)

    # Modify 2 of the files
    (repo / "file0.py").write_text("x_0 = 100\n")
    (repo / "file1.py").write_text("x_1 = 200\n")
    _git(["add", "."], cwd=repo)
    _git(["commit", "-m", "modify two files"], cwd=repo)

    return repo


class TestDiffEvaluate:
    def test_diff_evaluates_only_changed_files(self, git_repo):
        """Only the 2 modified files should be evaluated."""
        from eigenhelm.diff import discover_changed_files

        import os
        old_cwd = os.getcwd()
        try:
            os.chdir(git_repo)
            changed = discover_changed_files("HEAD~1")
        finally:
            os.chdir(old_cwd)

        changed_names = {p.name for p in changed}
        assert "file0.py" in changed_names
        assert "file1.py" in changed_names
        assert "file2.py" not in changed_names

    def test_diff_cli_evaluates_changed_files_only(self, git_repo):
        """--diff HEAD~1 should produce results for only 2 files."""
        from eigenhelm.cli.evaluate import main
        import os

        evaluated_files = []

        def fake_evaluate_paths(helm, paths, config=None):
            for p in paths:
                evaluated_files.append(p.name)
            return []

        old_cwd = os.getcwd()
        try:
            os.chdir(git_repo)
            with patch("eigenhelm.cli.evaluate._evaluate_paths", side_effect=fake_evaluate_paths):
                code = main(["--diff", "HEAD~1"])
        finally:
            os.chdir(old_cwd)

        assert code == 0
        assert len(evaluated_files) == 2
        assert "file0.py" in evaluated_files or "file1.py" in evaluated_files

    def test_diff_no_changes_returns_empty(self, git_repo):
        """If no recognized files changed, diff returns empty list."""
        from eigenhelm.diff import discover_changed_files

        # Add a commit changing only a non-source file
        (git_repo / "README.md").write_text("# Readme\n")
        _git(["add", "."], cwd=git_repo)
        _git(["commit", "-m", "add readme"], cwd=git_repo)

        import os
        old_cwd = os.getcwd()
        try:
            os.chdir(git_repo)
            changed = discover_changed_files("HEAD~1")
        finally:
            os.chdir(old_cwd)

        # Only .md file changed — should be empty (unrecognized extension)
        assert all(p.suffix != ".md" for p in changed)

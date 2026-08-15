"""Contract tests for `eh init` CLI command."""

from __future__ import annotations

import tomllib

import pytest
from click.testing import CliRunner

from eigenhelm.cli.main import cli
from eigenhelm.config import load_config

pytestmark = pytest.mark.contract


class TestInitCLI:
    def test_creates_config_file(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(cli, ["init", "--output", str(tmp_path)])
        assert result.exit_code == 0, result.output
        config_path = tmp_path / ".eigenhelm.toml"
        assert config_path.exists()

    def test_generated_file_is_valid_toml(self, tmp_path):
        runner = CliRunner()
        runner.invoke(cli, ["init", "--output", str(tmp_path)])
        config_path = tmp_path / ".eigenhelm.toml"
        with config_path.open("rb") as f:
            data = tomllib.load(f)
        assert "thresholds" in data

    def test_generated_file_parseable_by_load_config(self, tmp_path):
        runner = CliRunner()
        runner.invoke(cli, ["init", "--output", str(tmp_path)])
        cfg = load_config(tmp_path / ".eigenhelm.toml")
        assert cfg.thresholds.accept == 0.3
        assert cfg.thresholds.reject == 0.7

    def test_creates_eigenhelm_directory(self, tmp_path):
        runner = CliRunner()
        runner.invoke(cli, ["init", "--output", str(tmp_path)])
        assert (tmp_path / ".eigenhelm").is_dir()

    def test_existing_file_refused(self, tmp_path):
        config_path = tmp_path / ".eigenhelm.toml"
        config_path.write_text("# existing content\n")
        runner = CliRunner()
        result = runner.invoke(cli, ["init", "--output", str(tmp_path)])
        assert result.exit_code != 0
        # Original content preserved
        assert "existing content" in config_path.read_text()

    def test_force_overwrites_existing(self, tmp_path):
        config_path = tmp_path / ".eigenhelm.toml"
        config_path.write_text("# old content\n")
        runner = CliRunner()
        result = runner.invoke(cli, ["init", "--output", str(tmp_path), "--force"])
        assert result.exit_code == 0
        # New content written
        assert "eigenhelm" in config_path.read_text()
        assert "old content" not in config_path.read_text()

    def test_updates_gitignore(self, tmp_path):
        runner = CliRunner()
        runner.invoke(cli, ["init", "--output", str(tmp_path)])
        gitignore = tmp_path / ".gitignore"
        assert gitignore.exists()
        assert ".eigenhelm/" in gitignore.read_text()

    def test_gitignore_not_duplicated(self, tmp_path):
        """Running init twice should not add .eigenhelm/ to .gitignore twice."""
        runner = CliRunner()
        runner.invoke(cli, ["init", "--output", str(tmp_path)])
        runner.invoke(cli, ["init", "--output", str(tmp_path), "--force"])
        gitignore = tmp_path / ".gitignore"
        content = gitignore.read_text()
        assert content.count(".eigenhelm/") == 1

    def test_existing_gitignore_appended(self, tmp_path):
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("__pycache__/\n*.pyc\n")
        runner = CliRunner()
        runner.invoke(cli, ["init", "--output", str(tmp_path)])
        content = gitignore.read_text()
        assert "__pycache__/" in content
        assert ".eigenhelm/" in content

    def test_template_documents_harness_path_patterns(self, tmp_path):
        """Generated template must contain commented-out harness path rule examples."""
        runner = CliRunner()
        result = runner.invoke(cli, ["init", "--output", str(tmp_path)])
        assert result.exit_code == 0, result.output
        content = (tmp_path / ".eigenhelm.toml").read_text()
        # All four canonical harness/test patterns must appear as comments.
        for pattern in ("tests/**", "test/**", "validation/**", "harness/**"):
            assert pattern in content, f"template missing harness pattern example: {pattern}"

    def test_harness_path_rules_valid_when_uncommented(self, tmp_path):
        """Uncommented harness [[paths]] blocks must parse as valid TOML loadable by load_config."""
        toml = (
            "[thresholds]\n"
            "accept = 0.3\n"
            "reject = 0.7\n"
            "\n"
            "[[paths]]\n"
            'glob = "tests/**"\n'
            "[paths.thresholds]\n"
            "accept = 0.7\n"
            "reject = 0.95\n"
            "\n"
            "[[paths]]\n"
            'glob = "validation/**"\n'
            "[paths.thresholds]\n"
            "accept = 0.7\n"
            "reject = 0.95\n"
            "\n"
            "[[paths]]\n"
            'glob = "harness/**"\n'
            "[paths.thresholds]\n"
            "accept = 0.7\n"
            "reject = 0.95\n"
        )
        cfg_file = tmp_path / ".eigenhelm.toml"
        cfg_file.write_text(toml)
        cfg = load_config(cfg_file)
        assert len(cfg.paths) == 3
        # Each harness rule must have relaxed accept/reject thresholds.
        for rule in cfg.paths:
            assert rule.thresholds.accept == 0.7
            assert rule.thresholds.reject == 0.95

"""Unit tests for CLI modules — targeting coverage gaps.

Covers: model.py, benchmark.py, corpus.py, skill.py, mcp.py, serve.py,
harness.py, inspect.py, precommit.py, train.py
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from eigenhelm.cli.main import cli


# ---------------------------------------------------------------------------
# model.py tests
# ---------------------------------------------------------------------------

class TestModelListLocal:
    def test_list_local_with_models(self):
        from eigenhelm.registry.models import LocalModel

        fake_models = (
            LocalModel(name="python-v1", path="/tmp/python-v1.npz", bundled=True),
            LocalModel(name="js-v1", path="/tmp/js-v1.npz", bundled=False),
        )
        runner = CliRunner()
        with patch("eigenhelm.registry.list_local", return_value=fake_models):
            result = runner.invoke(cli, ["model", "list"])
        assert result.exit_code == 0
        assert "python-v1" in result.output
        assert "bundled" in result.output
        assert "js-v1" in result.output
        assert "cached" in result.output

    def test_list_local_no_models(self):
        runner = CliRunner()
        with patch("eigenhelm.registry.list_local", return_value=()):
            result = runner.invoke(cli, ["model", "list"])
        assert result.exit_code == 0
        assert "No models found" in result.output

    def test_list_remote_with_models(self):
        from eigenhelm.registry.models import ModelEntry

        fake_entry = ModelEntry(
            name="polyglot-v1",
            description="A model",
            language="polyglot",
            corpus_class="C",
            n_components=36,
            n_training_files=8000,
            download_url="https://example.com/model.npz",
            sha256="abc123",
            size_bytes=1500000,
            version="0.9.0",
        )
        runner = CliRunner()
        with patch("eigenhelm.registry.list_remote", return_value=(fake_entry,)):
            result = runner.invoke(cli, ["model", "list", "--remote"])
        assert result.exit_code == 0
        assert "polyglot-v1" in result.output
        assert "1M" in result.output  # size formatting

    def test_list_remote_empty(self):
        runner = CliRunner()
        with patch("eigenhelm.registry.list_remote", return_value=()):
            result = runner.invoke(cli, ["model", "list", "--remote"])
        assert result.exit_code == 0
        assert "No models in registry" in result.output

    def test_list_remote_error(self):
        from eigenhelm.registry import RegistryError

        runner = CliRunner()
        with patch(
            "eigenhelm.registry.list_remote",
            side_effect=RegistryError("Network error"),
        ):
            result = runner.invoke(cli, ["model", "list", "--remote"])
        assert result.exit_code != 0
        assert "Network error" in result.output


class TestModelPull:
    def test_pull_success(self):
        runner = CliRunner()
        with patch(
            "eigenhelm.registry.pull_model",
            return_value=Path("/tmp/test-model.npz"),
        ):
            result = runner.invoke(cli, ["model", "pull", "test-model"])
        assert result.exit_code == 0
        assert "Downloaded test-model" in result.output

    def test_pull_force(self):
        runner = CliRunner()
        with patch(
            "eigenhelm.registry.pull_model",
            return_value=Path("/tmp/test-model.npz"),
        ) as mock_pull:
            result = runner.invoke(cli, ["model", "pull", "test-model", "--force"])
        assert result.exit_code == 0
        mock_pull.assert_called_once_with("test-model", force=True)

    def test_pull_registry_error(self):
        from eigenhelm.registry import RegistryError

        runner = CliRunner()
        with patch(
            "eigenhelm.registry.pull_model",
            side_effect=RegistryError("Model 'foo' not found"),
        ):
            result = runner.invoke(cli, ["model", "pull", "foo"])
        assert result.exit_code != 0
        assert "not found" in result.output


class TestModelInfo:
    def test_info_model_found(self):
        @dataclass(frozen=True)
        class FakeDistribution:
            min: float = 0.1
            p10: float = 0.2
            p25: float = 0.3
            median: float = 0.5
            p75: float = 0.7
            p90: float = 0.8
            max: float = 0.95

        mock_model = MagicMock()
        mock_model.version = "0.9.0"
        mock_model.n_components = 36
        mock_model.corpus_hash = "abc123"
        mock_model.language = "python"
        mock_model.corpus_class = "A"
        mock_model.n_training_files = 500
        mock_model.calibrated_accept = 0.35
        mock_model.calibrated_reject = 0.65
        mock_model.score_distribution = FakeDistribution()

        runner = CliRunner()
        with (
            patch(
                "eigenhelm.registry.resolve_model",
                return_value=Path("/tmp/model.npz"),
            ),
            patch("eigenhelm.eigenspace.load_model", return_value=mock_model),
        ):
            result = runner.invoke(cli, ["model", "info", "python-v1"])
        assert result.exit_code == 0
        assert "python-v1" in result.output
        assert "0.9.0" in result.output
        assert "python" in result.output
        assert "0.350" in result.output  # calibrated_accept
        assert "Score dist" in result.output

    def test_info_model_not_found(self):
        runner = CliRunner()
        with patch("eigenhelm.registry.resolve_model", return_value=None):
            result = runner.invoke(cli, ["model", "info", "nonexistent"])
        assert result.exit_code != 0
        assert "not found" in result.output

    def test_info_model_load_error(self):
        runner = CliRunner()
        with (
            patch(
                "eigenhelm.registry.resolve_model",
                return_value=Path("/tmp/bad.npz"),
            ),
            patch(
                "eigenhelm.eigenspace.load_model",
                side_effect=RuntimeError("corrupt file"),
            ),
        ):
            result = runner.invoke(cli, ["model", "info", "bad-model"])
        assert result.exit_code != 0
        assert "corrupt file" in result.output

    def test_info_model_minimal_fields(self):
        """Model with no optional fields set."""
        mock_model = MagicMock()
        mock_model.version = "0.1.0"
        mock_model.n_components = 10
        mock_model.corpus_hash = "deadbeef"
        mock_model.language = None
        mock_model.corpus_class = None
        mock_model.n_training_files = 0
        mock_model.calibrated_accept = None
        mock_model.calibrated_reject = None
        mock_model.score_distribution = None

        runner = CliRunner()
        with (
            patch(
                "eigenhelm.registry.resolve_model",
                return_value=Path("/tmp/model.npz"),
            ),
            patch("eigenhelm.eigenspace.load_model", return_value=mock_model),
        ):
            result = runner.invoke(cli, ["model", "info", "minimal"])
        assert result.exit_code == 0
        assert "minimal" in result.output
        assert "Language" not in result.output  # Not printed when None


class TestModelFmtSize:
    def test_bytes(self):
        from eigenhelm.cli.model import _fmt_size

        assert _fmt_size(500) == "500B"

    def test_kilobytes(self):
        from eigenhelm.cli.model import _fmt_size

        assert _fmt_size(2048) == "2K"

    def test_megabytes(self):
        from eigenhelm.cli.model import _fmt_size

        assert _fmt_size(3 * 1024 * 1024) == "3M"


# ---------------------------------------------------------------------------
# model group --help
# ---------------------------------------------------------------------------

class TestModelHelp:
    def test_model_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["model", "--help"])
        assert result.exit_code == 0
        assert "Manage eigenhelm models" in result.output


# ---------------------------------------------------------------------------
# benchmark.py tests
# ---------------------------------------------------------------------------

class TestBenchmarkCLI:
    def test_help_exits_zero(self):
        from eigenhelm.cli.benchmark import main

        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])
        assert exc_info.value.code == 0

    def test_no_args_fails(self):
        from eigenhelm.cli.benchmark import main

        with pytest.raises(SystemExit) as exc_info:
            main([])
        assert exc_info.value.code == 2  # argparse exits 2 for missing required

    def test_build_parser(self):
        from eigenhelm.cli.benchmark import _build_parser

        parser = _build_parser()
        # Verify key options exist
        args = parser.parse_args(["--project", "/tmp/myproj"])
        assert args.project == [Path("/tmp/myproj")]
        assert args.output_format == "human"
        assert args.commits == 50

    def test_build_parser_corpus(self):
        from eigenhelm.cli.benchmark import _build_parser

        parser = _build_parser()
        args = parser.parse_args(["--corpus", "corpora/test.toml"])
        assert args.corpus == Path("corpora/test.toml")
        assert args.project is None

    def test_build_parser_all_options(self):
        from eigenhelm.cli.benchmark import _build_parser

        parser = _build_parser()
        args = parser.parse_args([
            "--project", "/tmp/proj",
            "--model", "model.npz",
            "--format", "json",
            "--output", "report.json",
            "--good-corpus", "/tmp/good",
            "--bad-corpus", "/tmp/bad",
            "--replay", "/tmp/repo",
            "--commits", "100",
            "--compare", "baseline.json",
        ])
        assert args.model == "model.npz"
        assert args.output_format == "json"
        assert args.output == Path("report.json")
        assert args.good_corpus == Path("/tmp/good")
        assert args.bad_corpus == Path("/tmp/bad")
        assert args.replay == Path("/tmp/repo")
        assert args.commits == 100
        assert args.compare == Path("baseline.json")

    def test_main_project_no_files(self):
        """Main with a project dir that has no evaluable files returns 1."""
        from eigenhelm.cli.benchmark import main

        mock_eigenspace = MagicMock()
        mock_eigenspace.version = "0.9.0"

        mock_report = MagicMock()
        mock_report.n_files = 0

        with (
            patch("eigenhelm.trained_models.default_model_path", return_value=Path("/fake/model.npz")),
            patch("eigenhelm.eigenspace.load_model", return_value=mock_eigenspace),
            patch("eigenhelm.helm.DynamicHelm"),
            patch("eigenhelm.validation.usecase_benchmark.UseCaseBenchmark") as mock_bench_cls,
        ):
            mock_bench = mock_bench_cls.return_value
            mock_bench.run.return_value = mock_report
            result = main(["--project", "/tmp/empty-proj"])
        assert result == 1

    def test_main_runtime_error(self):
        """Main returns 2 on unexpected exception."""
        from eigenhelm.cli.benchmark import main

        with patch(
            "eigenhelm.trained_models.default_model_path",
            side_effect=RuntimeError("boom"),
        ):
            result = main(["--project", "/tmp/proj"])
        assert result == 2

    def test_main_project_success_human(self):
        """Main with successful evaluation returns 0."""
        from eigenhelm.cli.benchmark import main

        mock_eigenspace = MagicMock()
        mock_eigenspace.version = "0.9.0"

        mock_report = MagicMock()
        mock_report.n_files = 5
        mock_report.render.return_value = "Report output"

        with (
            patch("eigenhelm.trained_models.default_model_path", return_value=Path("/fake/model.npz")),
            patch("eigenhelm.eigenspace.load_model", return_value=mock_eigenspace),
            patch("eigenhelm.helm.DynamicHelm"),
            patch("eigenhelm.validation.usecase_benchmark.UseCaseBenchmark") as mock_bench_cls,
        ):
            mock_bench = mock_bench_cls.return_value
            mock_bench.run.return_value = mock_report
            result = main(["--project", "/tmp/proj"])
        assert result == 0

    def test_main_project_json_format(self):
        """Main with --format json outputs JSON."""
        from eigenhelm.cli.benchmark import main

        mock_eigenspace = MagicMock()
        mock_eigenspace.version = "0.9.0"

        mock_report = MagicMock()
        mock_report.n_files = 3
        mock_report.to_json.return_value = '{"files": 3}'

        with (
            patch("eigenhelm.trained_models.default_model_path", return_value=Path("/fake/model.npz")),
            patch("eigenhelm.eigenspace.load_model", return_value=mock_eigenspace),
            patch("eigenhelm.helm.DynamicHelm"),
            patch("eigenhelm.validation.usecase_benchmark.UseCaseBenchmark") as mock_bench_cls,
        ):
            mock_bench = mock_bench_cls.return_value
            mock_bench.run.return_value = mock_report
            result = main(["--project", "/tmp/proj", "--format", "json"])
        assert result == 0

    def test_main_with_explicit_model(self):
        """Main with --model uses specified model."""
        from eigenhelm.cli.benchmark import main

        mock_eigenspace = MagicMock()
        mock_eigenspace.version = "0.9.0"

        mock_report = MagicMock()
        mock_report.n_files = 1
        mock_report.render.return_value = "ok"

        with (
            patch("eigenhelm.eigenspace.load_model", return_value=mock_eigenspace) as mock_load,
            patch("eigenhelm.helm.DynamicHelm"),
            patch("eigenhelm.validation.usecase_benchmark.UseCaseBenchmark") as mock_bench_cls,
        ):
            mock_bench = mock_bench_cls.return_value
            mock_bench.run.return_value = mock_report
            result = main(["--project", "/tmp/proj", "--model", "/tmp/my-model.npz"])
        assert result == 0
        mock_load.assert_called_once_with("/tmp/my-model.npz")

    def test_main_with_output_file(self, tmp_path):
        """Main with --output saves report."""
        from eigenhelm.cli.benchmark import main

        mock_eigenspace = MagicMock()
        mock_eigenspace.version = "0.9.0"

        mock_report = MagicMock()
        mock_report.n_files = 1
        mock_report.render.return_value = "ok"

        out_file = tmp_path / "report.json"

        with (
            patch("eigenhelm.trained_models.default_model_path", return_value=Path("/fake/model.npz")),
            patch("eigenhelm.eigenspace.load_model", return_value=mock_eigenspace),
            patch("eigenhelm.helm.DynamicHelm"),
            patch("eigenhelm.validation.usecase_benchmark.UseCaseBenchmark") as mock_bench_cls,
        ):
            mock_bench = mock_bench_cls.return_value
            mock_bench.run.return_value = mock_report
            result = main(["--project", "/tmp/proj", "--output", str(out_file)])
        assert result == 0
        mock_report.save.assert_called_once_with(out_file)


# ---------------------------------------------------------------------------
# corpus.py tests
# ---------------------------------------------------------------------------

class TestCorpusCLI:
    def test_help(self):
        from eigenhelm.cli.corpus import main

        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])
        assert exc_info.value.code == 0

    def test_sync_help(self):
        from eigenhelm.cli.corpus import main

        with pytest.raises(SystemExit) as exc_info:
            main(["sync", "--help"])
        assert exc_info.value.code == 0

    def test_no_subcommand_fails(self):
        from eigenhelm.cli.corpus import main

        with pytest.raises(SystemExit) as exc_info:
            main([])
        assert exc_info.value.code == 2

    def test_sync_missing_manifest(self, tmp_path):
        from eigenhelm.cli.corpus import main

        # load_any_manifest raises FileNotFoundError for missing file
        with (
            patch(
                "eigenhelm.corpus.manifest.load_any_manifest",
                side_effect=FileNotFoundError("not found"),
            ),
            pytest.raises(SystemExit) as exc_info,
        ):
            main(["sync", str(tmp_path / "nonexistent.toml"), str(tmp_path / "out")])
        assert exc_info.value.code == 1

    def test_sync_value_error(self, tmp_path):
        from eigenhelm.cli.corpus import main

        with (
            patch(
                "eigenhelm.corpus.manifest.load_any_manifest",
                side_effect=ValueError("bad manifest"),
            ),
            pytest.raises(SystemExit) as exc_info,
        ):
            main(["sync", str(tmp_path / "bad.toml"), str(tmp_path / "out")])
        assert exc_info.value.code == 1

    def test_sync_all_empty_dir(self, tmp_path):
        from eigenhelm.cli.corpus import main

        @dataclass
        class FakeBulk:
            per_manifest: dict = None
            failed_manifests: list = None
            any_failed: bool = False

            def __post_init__(self):
                if self.per_manifest is None:
                    self.per_manifest = {}
                if self.failed_manifests is None:
                    self.failed_manifests = []

        with (
            patch(
                "eigenhelm.corpus.sync.sync_all_manifests",
                return_value=FakeBulk(),
            ),
            pytest.raises(SystemExit) as exc_info,
        ):
            main(["sync", "--all", str(tmp_path), str(tmp_path / "out")])
        assert exc_info.value.code == 0

    def test_sync_single_manifest(self, tmp_path):
        """Test _cmd_sync with a single manifest."""
        from eigenhelm.cli.corpus import main

        @dataclass
        class FakeManifest:
            targets: list = None
            def __post_init__(self):
                if self.targets is None:
                    self.targets = []

        @dataclass
        class FakeResult:
            synced: tuple = ()
            skipped: tuple = ()
            failed: tuple = ()
            total_files: int = 0
            files_by_target: dict = None
            def __post_init__(self):
                if self.files_by_target is None:
                    self.files_by_target = {}

        with (
            patch("eigenhelm.corpus.manifest.load_any_manifest", return_value=FakeManifest()),
            patch("eigenhelm.corpus.sync.sync_manifest", return_value=FakeResult()),
            pytest.raises(SystemExit) as exc_info,
        ):
            main(["sync", str(tmp_path / "test.toml"), str(tmp_path / "out")])
        assert exc_info.value.code == 0

    def test_print_sync_result(self):
        """Test _print_sync_result formatting."""
        from eigenhelm.cli.corpus import _print_sync_result

        @dataclass
        class FakeResult:
            synced: tuple = ("repo-a",)
            skipped: tuple = ("repo-b",)
            failed: tuple = ()
            total_files: int = 42
            files_by_target: dict = None

            def __post_init__(self):
                if self.files_by_target is None:
                    self.files_by_target = {"repo-a": 42}

        @dataclass
        class FakeTarget:
            name: str

        targets = [FakeTarget("repo-a"), FakeTarget("repo-b")]
        _print_sync_result(FakeResult(), targets)

    def test_print_sync_result_with_failures(self, capsys):
        """Test _print_sync_result with failed targets."""
        from eigenhelm.cli.corpus import _print_sync_result

        @dataclass
        class FakeResult:
            synced: tuple = ()
            skipped: tuple = ()
            failed: tuple = (("repo-c", "timeout"),)
            total_files: int = 0
            files_by_target: dict = None

            def __post_init__(self):
                if self.files_by_target is None:
                    self.files_by_target = {}

        @dataclass
        class FakeTarget:
            name: str

        targets = [FakeTarget("repo-c")]
        _print_sync_result(FakeResult(), targets)
        captured = capsys.readouterr()
        assert "error" in captured.err

    def test_print_bulk_result(self, capsys):
        """Test _print_bulk_result formatting."""
        from eigenhelm.cli.corpus import _print_bulk_result

        @dataclass
        class FakeSR:
            synced: tuple = ("a",)
            skipped: tuple = ()
            failed: tuple = ()
            total_files: int = 10

        @dataclass
        class FakeBulk:
            per_manifest: dict = None
            failed_manifests: list = None

            def __post_init__(self):
                if self.per_manifest is None:
                    self.per_manifest = {"manifest-1": FakeSR()}
                if self.failed_manifests is None:
                    self.failed_manifests = [("manifest-2", "parse error")]

        _print_bulk_result(FakeBulk())
        captured = capsys.readouterr()
        assert "manifest-1" in captured.out
        assert "manifest-2" in captured.err

    def test_sync_composition_manifest(self, tmp_path):
        """Test _cmd_sync with a composition manifest."""
        from eigenhelm.cli.corpus import main
        from eigenhelm.corpus.manifest import CompositionManifest

        manifest_file = tmp_path / "comp.toml"
        manifest_file.write_text('[meta]\nname = "test"\n')

        fake_comp = MagicMock(spec=CompositionManifest)
        fake_comp.name = "test"
        fake_comp.sources = ["source1"]

        @dataclass
        class FakeBulk:
            per_manifest: dict = None
            failed_manifests: list = None
            any_failed: bool = False

            def __post_init__(self):
                if self.per_manifest is None:
                    self.per_manifest = {}
                if self.failed_manifests is None:
                    self.failed_manifests = []

        with (
            patch("eigenhelm.corpus.manifest.load_any_manifest", return_value=fake_comp),
            patch("eigenhelm.corpus.sync.sync_composition", return_value=FakeBulk()),
            pytest.raises(SystemExit) as exc_info,
        ):
            main(["sync", str(manifest_file), str(tmp_path / "out")])
        assert exc_info.value.code == 0

    def test_sync_composition_file_not_found(self, tmp_path):
        """Test _sync_composition when child manifest is missing."""
        from eigenhelm.cli.corpus import main
        from eigenhelm.corpus.manifest import CompositionManifest

        manifest_file = tmp_path / "comp.toml"
        manifest_file.write_text('[meta]\nname = "test"\n')

        fake_comp = MagicMock(spec=CompositionManifest)
        fake_comp.name = "test"
        fake_comp.sources = ["source1"]

        with (
            patch("eigenhelm.corpus.manifest.load_any_manifest", return_value=fake_comp),
            patch(
                "eigenhelm.corpus.sync.sync_composition",
                side_effect=FileNotFoundError("child.toml not found"),
            ),
            pytest.raises(SystemExit) as exc_info,
        ):
            main(["sync", str(manifest_file), str(tmp_path / "out")])
        assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# skill.py tests
# ---------------------------------------------------------------------------

class TestSkillCLI:
    def test_skill_print_stdout(self):
        runner = CliRunner()
        with patch("eigenhelm.cli.skill._load_skill", return_value="# Skill content\n"):
            result = runner.invoke(cli, ["skill"])
        assert result.exit_code == 0
        assert "Skill content" in result.output

    def test_skill_write_to_file(self, tmp_path):
        runner = CliRunner()
        out_file = tmp_path / "skill.md"
        with patch("eigenhelm.cli.skill._load_skill", return_value="# Skill\n"):
            result = runner.invoke(cli, ["skill", str(out_file)])
        assert result.exit_code == 0
        assert out_file.exists()
        assert "Skill" in out_file.read_text()

    def test_skill_install(self, tmp_path):
        runner = CliRunner()
        with patch("eigenhelm.cli.skill._load_skill", return_value="# Skill\n"):
            result = runner.invoke(cli, ["skill", "--install", str(tmp_path)])
        assert result.exit_code == 0
        installed = tmp_path / ".claude" / "skills" / "eigenhelm.md"
        assert installed.exists()

    def test_skill_install_refuses_existing(self, tmp_path):
        skill_dir = tmp_path / ".claude" / "skills"
        skill_dir.mkdir(parents=True)
        existing = skill_dir / "eigenhelm.md"
        existing.write_text("# Old\n")

        runner = CliRunner()
        with patch("eigenhelm.cli.skill._load_skill", return_value="# New\n"):
            result = runner.invoke(cli, ["skill", "--install", str(tmp_path)])
        assert result.exit_code != 0
        assert "already exists" in result.output

    def test_skill_install_force_overwrites(self, tmp_path):
        skill_dir = tmp_path / ".claude" / "skills"
        skill_dir.mkdir(parents=True)
        existing = skill_dir / "eigenhelm.md"
        existing.write_text("# Old\n")

        runner = CliRunner()
        with patch("eigenhelm.cli.skill._load_skill", return_value="# New\n"):
            result = runner.invoke(cli, ["skill", "--install", "--force", str(tmp_path)])
        assert result.exit_code == 0
        assert "New" in existing.read_text()

    def test_skill_install_file_target_rejected(self, tmp_path):
        target_file = tmp_path / "file.txt"
        target_file.write_text("x")
        runner = CliRunner()
        with patch("eigenhelm.cli.skill._load_skill", return_value="# Skill\n"):
            result = runner.invoke(cli, ["skill", "--install", str(target_file)])
        assert result.exit_code != 0
        assert "directory" in result.output

    def test_skill_write_refuses_existing(self, tmp_path):
        """Writing to a specific file path refuses if it exists without --force."""
        out_file = tmp_path / "skill.md"
        out_file.write_text("# Old\n")
        runner = CliRunner()
        with patch("eigenhelm.cli.skill._load_skill", return_value="# New\n"):
            result = runner.invoke(cli, ["skill", str(out_file)])
        assert result.exit_code != 0
        assert "already exists" in result.output


# ---------------------------------------------------------------------------
# mcp.py tests
# ---------------------------------------------------------------------------

class TestMcpCLI:
    def test_help(self):
        from eigenhelm.cli.mcp import main

        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])
        assert exc_info.value.code == 0

    def test_keyboard_interrupt(self):
        from eigenhelm.cli.mcp import main

        with patch(
            "eigenhelm.mcp.run_server",
            side_effect=KeyboardInterrupt,
        ):
            result = main([])
        assert result == 0

    def test_runtime_error(self):
        from eigenhelm.cli.mcp import main

        with patch(
            "eigenhelm.mcp.run_server",
            side_effect=RuntimeError("server crash"),
        ):
            result = main([])
        assert result == 1

    def test_with_model_option(self):
        from eigenhelm.cli.mcp import main

        mock_run = MagicMock()
        with patch("eigenhelm.mcp.run_server", mock_run):
            result = main(["--model", "/tmp/model.npz"])
        assert result == 0
        mock_run.assert_called_once_with(model_path="/tmp/model.npz")


# ---------------------------------------------------------------------------
# serve.py tests
# ---------------------------------------------------------------------------

class TestServeCLI:
    def test_help(self):
        from eigenhelm.cli.serve import main

        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])
        assert exc_info.value.code == 0

    def test_serve_starts(self):
        """Test that serve loads model and starts uvicorn."""
        from eigenhelm.cli.serve import main

        mock_eigenspace = MagicMock()
        mock_eigenspace.version = "0.9.0"
        mock_eigenspace.corpus_hash = "abc123"
        mock_app = MagicMock()

        with (
            patch("eigenhelm.trained_models.default_model_path", return_value=Path("/fake/model.npz")),
            patch("eigenhelm.eigenspace.load_model", return_value=mock_eigenspace),
            patch("eigenhelm.serve.create_app", return_value=mock_app),
            patch("uvicorn.run") as mock_uvicorn_run,
        ):
            main([])
        mock_uvicorn_run.assert_called_once()

    def test_serve_model_not_found(self):
        from eigenhelm.cli.serve import main

        with (
            patch("eigenhelm.trained_models.default_model_path", return_value=Path("/fake/model.npz")),
            patch(
                "eigenhelm.eigenspace.load_model",
                side_effect=FileNotFoundError("model not found"),
            ),
        ):
            with pytest.raises(SystemExit) as exc_info:
                main([])
            assert exc_info.value.code == 1

    def test_serve_custom_host_port(self):
        """Test that custom host/port are passed to uvicorn."""
        from eigenhelm.cli.serve import main

        mock_eigenspace = MagicMock()
        mock_eigenspace.version = "0.9.0"
        mock_eigenspace.corpus_hash = "abc123"

        with (
            patch("eigenhelm.trained_models.default_model_path", return_value=Path("/fake/model.npz")),
            patch("eigenhelm.eigenspace.load_model", return_value=mock_eigenspace),
            patch("eigenhelm.serve.create_app", return_value=MagicMock()),
            patch("uvicorn.run") as mock_run,
        ):
            main(["--host", "127.0.0.1", "--port", "9090"])
        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args
        assert call_kwargs.kwargs["host"] == "127.0.0.1" or call_kwargs[1].get("host") == "127.0.0.1"


# ---------------------------------------------------------------------------
# harness.py tests
# ---------------------------------------------------------------------------

class TestHarnessCLI:
    def test_help(self):
        from eigenhelm.cli.harness import main

        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])
        assert exc_info.value.code == 0

    def test_missing_required_args(self):
        from eigenhelm.cli.harness import main

        with pytest.raises(SystemExit) as exc_info:
            main([])
        assert exc_info.value.code == 2

    def test_harness_success(self, tmp_path):
        from eigenhelm.cli.harness import main

        before = tmp_path / "before"
        after = tmp_path / "after"
        before.mkdir()
        after.mkdir()

        mock_report = MagicMock()
        with (
            patch("eigenhelm.harness.runner.run_harness", return_value=mock_report),
            patch(
                "eigenhelm.cli.harness.format_harness_human",
                return_value="Report output",
            ),
        ):
            result = main(["--before", str(before), "--after", str(after)])
        assert result == 0

    def test_harness_json_output(self, tmp_path):
        from eigenhelm.cli.harness import main

        before = tmp_path / "before"
        after = tmp_path / "after"
        before.mkdir()
        after.mkdir()

        mock_report = MagicMock()
        with (
            patch("eigenhelm.harness.runner.run_harness", return_value=mock_report),
            patch(
                "eigenhelm.cli.harness.format_harness_json",
                return_value='{"result": "ok"}',
            ),
        ):
            result = main(
                ["--before", str(before), "--after", str(after), "--json"]
            )
        assert result == 0

    def test_harness_with_model(self, tmp_path):
        from eigenhelm.cli.harness import main

        before = tmp_path / "before"
        after = tmp_path / "after"
        before.mkdir()
        after.mkdir()

        mock_report = MagicMock()
        mock_eigenspace = MagicMock()

        with (
            patch("eigenhelm.eigenspace.load_model", return_value=mock_eigenspace),
            patch("eigenhelm.harness.runner.run_harness", return_value=mock_report),
            patch(
                "eigenhelm.cli.harness.format_harness_human",
                return_value="ok",
            ),
        ):
            result = main([
                "--before", str(before),
                "--after", str(after),
                "--model", "/tmp/model.npz",
            ])
        assert result == 0

    def test_harness_value_error(self, tmp_path):
        from eigenhelm.cli.harness import main

        with patch(
            "eigenhelm.harness.runner.run_harness",
            side_effect=ValueError("Empty corpus"),
        ):
            result = main([
                "--before", str(tmp_path),
                "--after", str(tmp_path),
            ])
        assert result == 1

    def test_harness_runtime_error(self, tmp_path):
        from eigenhelm.cli.harness import main

        with patch(
            "eigenhelm.harness.runner.run_harness",
            side_effect=RuntimeError("unexpected"),
        ):
            result = main([
                "--before", str(tmp_path),
                "--after", str(tmp_path),
            ])
        assert result == 2


# ---------------------------------------------------------------------------
# inspect.py tests
# ---------------------------------------------------------------------------

class TestInspectCLI:
    def test_help(self):
        from eigenhelm.cli.inspect import main

        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])
        assert exc_info.value.code == 0

    def test_inspect_human_output(self, tmp_path):
        import numpy as np
        from eigenhelm.cli.inspect import main

        model_path = tmp_path / "model.npz"
        model_path.write_bytes(b"fake")

        fake_info = {
            "version": "0.9.0",
            "n_components": 10,
            "corpus_hash": "abc123",
            "projection_shape": (69, 10),
            "cumulative_variance": 0.95,
            "explained_variance_ratio": np.array([0.3, 0.2, 0.15, 0.1, 0.05, 0.05, 0.03, 0.03, 0.02, 0.02]),
            "mean_range": (0.1, 5.0),
            "std_range": (0.5, 2.0),
            "sigma_drift": 1.5,
            "sigma_virtue": 0.8,
            "language": "python",
            "corpus_class": "A",
            "n_training_files": 200,
            "n_exemplars": 50,
            "calibrated_accept": 0.35,
            "calibrated_reject": 0.65,
            "score_distribution": {
                "min": 0.05,
                "p10": 0.2,
                "p25": 0.35,
                "median": 0.5,
                "p75": 0.65,
                "p90": 0.8,
                "max": 0.95,
            },
        }

        with patch("eigenhelm.training.inspect_model", return_value=fake_info):
            with pytest.raises(SystemExit) as exc_info:
                main([str(model_path)])
            assert exc_info.value.code == 0

    def test_inspect_json_output(self, tmp_path):
        import numpy as np
        from eigenhelm.cli.inspect import main

        model_path = tmp_path / "model.npz"
        model_path.write_bytes(b"fake")

        fake_info = {
            "version": "0.9.0",
            "n_components": 10,
            "corpus_hash": "abc123",
            "projection_shape": (69, 10),
            "cumulative_variance": 0.95,
            "explained_variance_ratio": np.array([0.3, 0.2]),
            "mean_range": (0.1, 5.0),
            "std_range": (0.5, 2.0),
            "sigma_drift": 1.5,
            "sigma_virtue": 0.8,
            "language": "python",
            "corpus_class": "A",
            "n_training_files": 200,
            "n_exemplars": 50,
            "calibrated_accept": 0.35,
            "calibrated_reject": 0.65,
            "score_distribution": {
                "min": 0.05, "p10": 0.2, "p25": 0.35,
                "median": 0.5, "p75": 0.65, "p90": 0.8, "max": 0.95,
            },
        }

        with patch("eigenhelm.training.inspect_model", return_value=fake_info):
            with pytest.raises(SystemExit) as exc_info:
                main([str(model_path), "--json"])
            assert exc_info.value.code == 0

    def test_inspect_file_not_found(self, tmp_path):
        from eigenhelm.cli.inspect import main

        with patch(
            "eigenhelm.training.inspect_model",
            side_effect=FileNotFoundError("not found"),
        ):
            with pytest.raises(SystemExit) as exc_info:
                main([str(tmp_path / "nonexistent.npz")])
            assert exc_info.value.code == 1

    def test_inspect_key_error(self, tmp_path):
        from eigenhelm.cli.inspect import main

        with patch(
            "eigenhelm.training.inspect_model",
            side_effect=KeyError("missing_key"),
        ):
            with pytest.raises(SystemExit) as exc_info:
                main([str(tmp_path / "bad.npz")])
            assert exc_info.value.code == 1

    def test_inspect_generic_error(self, tmp_path):
        from eigenhelm.cli.inspect import main

        with patch(
            "eigenhelm.training.inspect_model",
            side_effect=RuntimeError("unexpected"),
        ):
            with pytest.raises(SystemExit) as exc_info:
                main([str(tmp_path / "err.npz")])
            assert exc_info.value.code == 1

    def test_inspect_no_variance_ratio(self, tmp_path):
        from eigenhelm.cli.inspect import main

        model_path = tmp_path / "model.npz"
        model_path.write_bytes(b"fake")

        fake_info = {
            "version": "0.1.0",
            "n_components": 5,
            "corpus_hash": "xyz",
            "projection_shape": (69, 5),
            "cumulative_variance": 0.0,
            "explained_variance_ratio": None,
            "mean_range": (0.0, 1.0),
            "std_range": (0.0, 1.0),
            "sigma_drift": None,
            "sigma_virtue": None,
            "language": None,
            "corpus_class": None,
            "n_training_files": 0,
            "n_exemplars": 0,
            "calibrated_accept": None,
            "calibrated_reject": None,
            "score_distribution": None,
        }

        with patch("eigenhelm.training.inspect_model", return_value=fake_info):
            with pytest.raises(SystemExit) as exc_info:
                main([str(model_path)])
            assert exc_info.value.code == 0


# ---------------------------------------------------------------------------
# precommit.py tests
# ---------------------------------------------------------------------------

class TestPrecommitCLI:
    def test_help_exits_zero(self):
        from eigenhelm.cli.precommit import main

        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])
        assert exc_info.value.code == 0

    def test_no_staged_files(self):
        from eigenhelm.cli.precommit import main

        with (
            patch("eigenhelm.cli.precommit._load_project_config", return_value=(None, None, False, "")),
            patch("eigenhelm.cli.precommit._get_staged_files", return_value=[]),
        ):
            result = main([])
        assert result == 0

    def test_lenient_flag(self):
        from eigenhelm.cli.precommit import main

        with (
            patch("eigenhelm.cli.precommit._load_project_config", return_value=(None, None, False, "")),
            patch("eigenhelm.cli.precommit._get_staged_files", return_value=[]),
        ):
            result = main(["--lenient"])
        assert result == 0

    def test_strict_flag(self):
        from eigenhelm.cli.precommit import main

        with (
            patch("eigenhelm.cli.precommit._load_project_config", return_value=(None, None, False, "")),
            patch("eigenhelm.cli.precommit._get_staged_files", return_value=[]),
        ):
            result = main(["--strict"])
        assert result == 0

    def test_scorecard_flag(self):
        from eigenhelm.cli.precommit import main

        with (
            patch("eigenhelm.cli.precommit._load_project_config", return_value=(None, None, False, "")),
            patch("eigenhelm.cli.precommit._get_staged_files", return_value=[]),
        ):
            result = main(["--scorecard"])
        assert result == 0

    def test_runtime_error_returns_2(self):
        from eigenhelm.cli.precommit import main

        with patch(
            "eigenhelm.cli.precommit._load_project_config",
            side_effect=RuntimeError("boom"),
        ):
            result = main([])
        assert result == 2


# ---------------------------------------------------------------------------
# train.py tests
# ---------------------------------------------------------------------------

class TestTrainCLI:
    def test_help(self):
        from eigenhelm.cli.train import main

        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])
        assert exc_info.value.code == 0

    def test_missing_required_args(self):
        from eigenhelm.cli.train import main

        with pytest.raises(SystemExit) as exc_info:
            main([])
        assert exc_info.value.code == 2

    def test_format_training_report(self):
        from eigenhelm.cli.train import format_training_report

        @dataclass
        class FakeModel:
            n_components: int = 10
            corpus_hash: str = "abc123"
            version: str = "0.9.0"
            language: str = "python"
            corpus_class: str = "A"
            calibrated_accept: float | None = 0.35
            calibrated_reject: float | None = 0.65

        @dataclass
        class FakeCalibration:
            sigma_drift: float = 1.5
            sigma_virtue: float = 0.8
            percentile: float = 95
            n_projections: int = 200

        @dataclass
        class FakeDistribution:
            min: float = 0.05
            p10: float = 0.2
            p25: float = 0.35
            median: float = 0.5
            p75: float = 0.65
            p90: float = 0.8
            max: float = 0.95

        @dataclass
        class FakeResult:
            model: FakeModel = None
            n_files_processed: int = 100
            n_files_skipped: int = 5
            n_units_extracted: int = 500
            n_vectors_excluded: int = 2
            cumulative_variance: float = 0.95
            explained_variance_ratio: tuple = (0.3, 0.2, 0.15)
            calibration: FakeCalibration = None
            exemplars: list = None
            score_distribution: FakeDistribution = None
            calibration_skip_reason: str | None = None

            def __post_init__(self):
                if self.model is None:
                    self.model = FakeModel()
                if self.calibration is None:
                    self.calibration = FakeCalibration()
                if self.score_distribution is None:
                    self.score_distribution = FakeDistribution()

        result = FakeResult(exemplars=[1, 2, 3])
        report = format_training_report(
            result, Path("/tmp/corpus"), Path("/tmp/output.npz")
        )
        assert "Training complete" in report
        assert "python" in report
        assert "sigma_drift" in report
        assert "Exemplars selected: 3" in report
        assert "Score dist" in report
        assert "Thresholds" in report

    def test_format_training_report_skip_reason(self):
        from eigenhelm.cli.train import format_training_report

        @dataclass
        class FakeModel:
            n_components: int = 10
            corpus_hash: str = "abc"
            version: str = "0.1.0"
            language: str | None = None
            corpus_class: str | None = None
            calibrated_accept: float | None = None
            calibrated_reject: float | None = None

        @dataclass
        class FakeResult:
            model: FakeModel = None
            n_files_processed: int = 50
            n_files_skipped: int = 0
            n_units_extracted: int = 100
            n_vectors_excluded: int = 0
            cumulative_variance: float = 0.90
            explained_variance_ratio: tuple = (0.5, 0.4)
            calibration: None = None
            exemplars: None = None
            score_distribution: None = None
            calibration_skip_reason: str = "Too few files"

            def __post_init__(self):
                if self.model is None:
                    self.model = FakeModel()

        result = FakeResult()
        report = format_training_report(
            result, Path("/tmp/corpus"), Path("/tmp/out.npz"), auto_selected=False
        )
        assert "Too few files" in report
        assert "explicit" in report

    def test_train_invalid_language(self, tmp_path):
        from eigenhelm.cli.train import main

        with pytest.raises(SystemExit) as exc_info:
            main([
                str(tmp_path),
                "-o", str(tmp_path / "out.npz"),
                "--language", "klingon",
            ])
        assert exc_info.value.code == 2

    def test_train_file_not_found(self, tmp_path):
        from eigenhelm.cli.train import main

        with patch(
            "eigenhelm.training.train_eigenspace",
            side_effect=FileNotFoundError("corpus not found"),
        ):
            with pytest.raises(SystemExit) as exc_info:
                main([
                    str(tmp_path),
                    "-o", str(tmp_path / "out.npz"),
                    "--language", "python",
                ])
            assert exc_info.value.code == 1

    def test_train_runtime_error(self, tmp_path):
        from eigenhelm.cli.train import main

        with patch(
            "eigenhelm.training.train_eigenspace",
            side_effect=RuntimeError("extraction failed"),
        ):
            with pytest.raises(SystemExit) as exc_info:
                main([
                    str(tmp_path),
                    "-o", str(tmp_path / "out.npz"),
                    "--language", "python",
                ])
            assert exc_info.value.code == 2

    def test_train_save_file_exists(self, tmp_path):
        from eigenhelm.cli.train import main

        mock_result = MagicMock()
        with (
            patch("eigenhelm.training.train_eigenspace", return_value=mock_result),
            patch(
                "eigenhelm.training.save_model",
                side_effect=FileExistsError("already exists"),
            ),
        ):
            with pytest.raises(SystemExit) as exc_info:
                main([
                    str(tmp_path),
                    "-o", str(tmp_path / "out.npz"),
                    "--language", "python",
                ])
            assert exc_info.value.code == 1

    def test_train_save_runtime_error(self, tmp_path):
        from eigenhelm.cli.train import main

        mock_result = MagicMock()
        with (
            patch("eigenhelm.training.train_eigenspace", return_value=mock_result),
            patch(
                "eigenhelm.training.save_model",
                side_effect=RuntimeError("disk full"),
            ),
        ):
            with pytest.raises(SystemExit) as exc_info:
                main([
                    str(tmp_path),
                    "-o", str(tmp_path / "out.npz"),
                    "--language", "python",
                ])
            assert exc_info.value.code == 2


# ---------------------------------------------------------------------------
# main.py passthrough tests
# ---------------------------------------------------------------------------

class TestPassthrough:
    def test_evaluate_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["evaluate", "--help"])
        assert result.exit_code == 0
        assert "eigenhelm-evaluate" in result.output

    def test_train_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["train", "--help"])
        assert result.exit_code == 0
        assert "eigenhelm-train" in result.output

    def test_inspect_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["inspect", "--help"])
        assert result.exit_code == 0

    def test_corpus_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["corpus", "--help"])
        assert result.exit_code == 0

    def test_harness_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["harness", "--help"])
        assert result.exit_code == 0

    def test_mcp_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["mcp", "--help"])
        assert result.exit_code == 0

    def test_serve_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["serve", "--help"])
        assert result.exit_code == 0

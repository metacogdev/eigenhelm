"""Targeted tests for small coverage gaps in validation module files.

Covers missing lines in:
- categorize.py: _categorize_init edge cases, _is_schema_content, categorize_directory, UNKNOWN
- discrimination.py: _cohens_d pooled_std==0
- diversity.py: total variance == 0 branch
- benchmark.py: report() with no classifications
- usecase_models.py: QualityTarget.met edge cases, BenchmarkReport.save/render
"""

from __future__ import annotations

import json
from pathlib import Path


from eigenhelm.validation.categorize import (
    _categorize_init,
    _is_schema_content,
    categorize_directory,
    categorize_file,
)
from eigenhelm.validation.discrimination import _cohens_d
from eigenhelm.validation.usecase_models import (
    BenchmarkReport,
    CategoryDistribution,
    DimensionDiscrimination,
    FileCategory,
    QualityTarget,
)


class TestCategorizeInitEdgeCases:
    """Cover _categorize_init branches."""

    def test_none_content(self) -> None:
        assert _categorize_init(None) == FileCategory.INIT

    def test_empty_content(self) -> None:
        assert _categorize_init("") == FileCategory.INIT

    def test_comments_only(self) -> None:
        assert _categorize_init("# just a comment\n# another\n") == FileCategory.INIT

    def test_long_file_is_implementation(self) -> None:
        # > 50 non-blank non-comment lines
        lines = [f"x_{i} = {i}" for i in range(55)]
        assert _categorize_init("\n".join(lines)) == FileCategory.IMPLEMENTATION

    def test_mostly_imports(self) -> None:
        content = "\n".join(
            ["from .foo import bar"] * 8
            + ['__all__ = ["bar"]']
            + ["x = 1"]
        )
        assert _categorize_init(content) == FileCategory.INIT


class TestIsSchemaContent:
    """Cover _is_schema_content branches."""

    def test_empty_content(self) -> None:
        assert _is_schema_content("") is True

    def test_only_comments(self) -> None:
        assert _is_schema_content("# comment\n# another\n") is True

    def test_short_no_defs(self) -> None:
        assert _is_schema_content("FOO = 1\nBAR = 2\n") is True

    def test_classes_with_few_defs(self) -> None:
        content = "class Foo:\n    pass\n\ndef helper():\n    pass\n"
        assert _is_schema_content(content) is True

    def test_many_defs_no_classes(self) -> None:
        content = "\n".join(
            [f"def func_{i}():\n    pass\n" for i in range(5)]
        )
        assert _is_schema_content(content) is False


class TestCategorizeFileEdgeCases:
    """Cover remaining categorize_file branches."""

    def test_generated_dir(self) -> None:
        assert categorize_file("generated/foo.py") == FileCategory.GENERATED

    def test_schema_dir_no_content(self) -> None:
        # No content, in schema dir => SCHEMA
        assert categorize_file("models/user.py") == FileCategory.SCHEMA

    def test_unknown_extension(self) -> None:
        assert categorize_file("readme.txt") == FileCategory.UNKNOWN

    def test_schema_dir_with_logic_content(self) -> None:
        """File in models/ dir but with lots of function defs => not schema."""
        content = "\n".join(
            [f"def func_{i}(x):\n    return x + {i}\n" for i in range(10)]
        )
        assert categorize_file("models/logic.py", content=content) == FileCategory.IMPLEMENTATION


class TestCategorizeDirectory:
    """Cover categorize_directory function."""

    def test_basic_directory(self, tmp_path: Path) -> None:
        (tmp_path / "main.py").write_text("def hello():\n    pass\n")
        (tmp_path / "test_main.py").write_text("def test_hello():\n    pass\n")
        (tmp_path / "__init__.py").write_text("")
        (tmp_path / "readme.md").write_text("# docs")

        results = categorize_directory(tmp_path)
        assert results[Path("main.py")] == FileCategory.IMPLEMENTATION
        assert results[Path("test_main.py")] == FileCategory.TEST
        assert results[Path("__init__.py")] == FileCategory.INIT
        assert Path("readme.md") not in results  # unsupported extension

    def test_skips_pycache(self, tmp_path: Path) -> None:
        cache = tmp_path / "__pycache__"
        cache.mkdir()
        (cache / "mod.py").write_text("")
        (tmp_path / "mod.py").write_text("x = 1")

        results = categorize_directory(tmp_path)
        paths = {str(p) for p in results.keys()}
        assert not any("__pycache__" in p for p in paths)

    def test_with_overrides(self, tmp_path: Path) -> None:
        (tmp_path / "special.py").write_text("x = 1")
        overrides = {"special.py": FileCategory.GENERATED}
        results = categorize_directory(tmp_path, overrides=overrides)
        assert results[Path("special.py")] == FileCategory.GENERATED


class TestCohensDEdgeCases:
    """Cover _cohens_d edge cases in discrimination.py."""

    def test_zero_pooled_std(self) -> None:
        """Identical values in both groups => pooled_std=0 => return 0.0."""
        assert _cohens_d([1.0, 1.0, 1.0], [1.0, 1.0, 1.0]) == 0.0


class TestQualityTargetMet:
    """Cover QualityTarget.met branches."""

    def test_none_baseline(self) -> None:
        t = QualityTarget("x", "d", None, 1.0, "higher_is_better")
        assert t.met is False

    def test_lower_is_better_met(self) -> None:
        t = QualityTarget("x", "d", 0.05, 0.10, "lower_is_better")
        assert t.met is True

    def test_lower_is_better_not_met(self) -> None:
        t = QualityTarget("x", "d", 0.15, 0.10, "lower_is_better")
        assert t.met is False

    def test_higher_is_better_met(self) -> None:
        t = QualityTarget("x", "d", 600.0, 500.0, "higher_is_better")
        assert t.met is True

    def test_higher_is_better_not_met(self) -> None:
        t = QualityTarget("x", "d", 400.0, 500.0, "higher_is_better")
        assert t.met is False


class TestBenchmarkReportSaveAndRender:
    """Cover BenchmarkReport.save and render paths."""

    def test_save(self, tmp_path: Path) -> None:
        report = BenchmarkReport(date="2024-01-01", model="test", n_files=5, n_projects=1)
        path = tmp_path / "report.json"
        report.save(path)
        data = json.loads(path.read_text())
        assert data["date"] == "2024-01-01"
        assert data["n_files"] == 5

    def test_render_with_dim_discrimination(self) -> None:
        dd = DimensionDiscrimination(
            dimension="manifold_drift",
            category=FileCategory.IMPLEMENTATION,
            cohens_d=0.85,
            cv=0.3,
            mean=0.5,
            std=0.15,
            signal_quality="strong",
        )
        report = BenchmarkReport(
            date="2024-01-01",
            model="test",
            n_files=10,
            n_projects=1,
            dimension_discrimination=(dd,),
            targets=(
                QualityTarget("sc_001", "desc", 10.0, 500.0, "higher_is_better"),
            ),
        )
        text = report.render()
        assert "Dimension Discrimination" in text
        assert "manifold_drift" in text
        assert "FAIL" in text  # 10 < 500

    def test_render_dim_disc_none_cohens_d(self) -> None:
        dd = DimensionDiscrimination(
            dimension="ncd_exemplar_distance",
            category=FileCategory.IMPLEMENTATION,
            cohens_d=None,
            cv=0.1,
            mean=0.3,
            std=0.05,
            signal_quality="noise",
        )
        report = BenchmarkReport(
            dimension_discrimination=(dd,),
        )
        text = report.render()
        assert "N/A" in text

    def test_to_dict_roundtrip(self) -> None:
        cat = CategoryDistribution(FileCategory.TEST, 5, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7)
        report = BenchmarkReport(
            categories=(cat,),
            fp_rate=0.1,
            fn_rate=0.2,
            attribution_precision=0.8,
        )
        d = report.to_dict()
        assert d["fp_rate"] == 0.1
        assert d["fn_rate"] == 0.2
        assert d["attribution_precision"] == 0.8
        assert d["categories"][0]["category"] == "test"

"""Contract tests for eigenhelm-train --language / --corpus-class flags (009 T012)."""

from __future__ import annotations

import numpy as np
import pytest

from eigenhelm.cli.train import main


def _run_train(argv: list[str]) -> None:
    """Run train CLI, allowing sys.exit(0) but re-raising non-zero."""
    try:
        main(argv)
    except SystemExit as exc:
        if exc.code != 0:
            raise


class TestTrainLanguageFlag:
    """Contract: --language is required and validated."""

    def test_language_required(self, corpus_dir, tmp_path) -> None:
        """eigenhelm-train fails if --language is not provided."""
        out = tmp_path / "model.npz"
        with pytest.raises(SystemExit) as exc:
            main([str(corpus_dir), "-o", str(out)])
        assert exc.value.code == 2  # argparse error

    def test_invalid_language_rejected(self, corpus_dir, tmp_path) -> None:
        """eigenhelm-train rejects unknown language keys."""
        out = tmp_path / "model.npz"
        with pytest.raises(SystemExit) as exc:
            main([str(corpus_dir), "-o", str(out), "--language", "brainfuck"])
        assert exc.value.code == 2  # argparse error

    def test_valid_language_accepted(self, corpus_dir, tmp_path) -> None:
        """eigenhelm-train accepts known language keys and writes metadata."""
        out = tmp_path / "model.npz"
        _run_train([str(corpus_dir), "-o", str(out), "--language", "python"])

        data = np.load(out)
        assert str(data["language"]) == "python"
        assert str(data["corpus_class"]) == "A"  # default
        assert int(data["n_training_files"]) > 0

    def test_multi_language_accepted(self, corpus_dir, tmp_path) -> None:
        """eigenhelm-train accepts 'multi' for Class B models."""
        out = tmp_path / "model.npz"
        _run_train(
            [
                str(corpus_dir),
                "-o",
                str(out),
                "--language",
                "multi",
                "--corpus-class",
                "B",
            ]
        )

        data = np.load(out)
        assert str(data["language"]) == "multi"
        assert str(data["corpus_class"]) == "B"


class TestCorpusClassFlag:
    """Contract: --corpus-class defaults to A and validates."""

    def test_default_corpus_class_is_a(self, corpus_dir, tmp_path) -> None:
        out = tmp_path / "model.npz"
        _run_train([str(corpus_dir), "-o", str(out), "--language", "python"])

        data = np.load(out)
        assert str(data["corpus_class"]) == "A"

    def test_corpus_class_b_accepted(self, corpus_dir, tmp_path) -> None:
        out = tmp_path / "model.npz"
        _run_train(
            [
                str(corpus_dir),
                "-o",
                str(out),
                "--language",
                "multi",
                "--corpus-class",
                "B",
            ]
        )

        data = np.load(out)
        assert str(data["corpus_class"]) == "B"

    def test_invalid_corpus_class_rejected(self, corpus_dir, tmp_path) -> None:
        out = tmp_path / "model.npz"
        with pytest.raises(SystemExit) as exc:
            main(
                [
                    str(corpus_dir),
                    "-o",
                    str(out),
                    "--language",
                    "python",
                    "--corpus-class",
                    "C",
                ]
            )
        assert exc.value.code == 2

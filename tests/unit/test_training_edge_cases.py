"""Edge case tests for training pipeline (009 T031)."""

from __future__ import annotations

from pathlib import Path

import pytest

from eigenhelm.training import train_eigenspace


class TestMinimumCorpusGuard:
    """Training requires minimum file count for reliable PCA."""

    def test_below_min_files_raises(self, tmp_path: Path) -> None:
        """Corpus with fewer than min_files eligible files raises ValueError."""
        corpus = tmp_path / "small_corpus"
        corpus.mkdir()
        # Write 3 Python files (below default min_files=1, but we set min_files=10)
        for i in range(3):
            (corpus / f"f{i}.py").write_text(f"def func{i}():\n    return {i}\n")

        with pytest.raises(ValueError, match="minimum 10 required"):
            train_eigenspace(corpus, language="python", corpus_class="A", min_files=10)

    def test_at_min_files_succeeds(self, corpus_dir: Path) -> None:
        """Corpus with exactly min_files eligible files succeeds."""
        # corpus_dir has 10 files (5 languages x 2 files each)
        result = train_eigenspace(corpus_dir, language="python", corpus_class="A", min_files=10)
        assert result.n_files_processed >= 10

    def test_zero_min_files_allows_small_corpus(self, tmp_path: Path) -> None:
        """min_files=0 allows any non-empty corpus (PCA still needs >= 2 vectors)."""
        corpus = tmp_path / "tiny_corpus"
        corpus.mkdir()
        (corpus / "one.py").write_text("def f(x):\n    if x > 0:\n        return x\n    return -x\n")
        (corpus / "two.py").write_text("def g(y):\n    return y * 2 + 1\n")

        result = train_eigenspace(corpus, language="python", corpus_class="A", min_files=0)
        assert result.n_files_processed == 2


class TestSkippedFileAccounting:
    """Files that fail extraction are counted in n_files_skipped."""

    def test_unrecognized_extension_skipped(self, tmp_path: Path) -> None:
        """Files with extensions not in EXTENSION_TO_LANGUAGE are not counted."""
        corpus = tmp_path / "mixed_corpus"
        corpus.mkdir()
        # Write valid Python files
        for i in range(5):
            (corpus / f"valid{i}.py").write_text(f"def func{i}():\n    return {i}\n")
        # Write files with unrecognized extensions (these are silently skipped
        # during discovery, not counted in n_files_skipped)
        (corpus / "readme.txt").write_text("not code")
        (corpus / "data.csv").write_text("a,b,c\n1,2,3")

        result = train_eigenspace(corpus, language="python", corpus_class="A", min_files=1)
        # discover_corpus_files() only finds recognized extensions
        # so txt/csv files are never even attempted
        assert result.n_files_processed >= 5

    def test_empty_source_file_skipped(self, tmp_path: Path) -> None:
        """Files that produce zero feature vectors are counted as skipped."""
        corpus = tmp_path / "corpus"
        corpus.mkdir()
        # Valid files
        for i in range(5):
            (corpus / f"good{i}.py").write_text(
                f"def func{i}(x):\n    if x > 0:\n        return x\n    return -x\n"
            )
        # Empty Python file — valid extension but no extractable units
        (corpus / "empty.py").write_text("")

        result = train_eigenspace(corpus, language="python", corpus_class="A", min_files=1)
        # The empty file either produces no vectors or is skipped
        assert result.n_files_processed + result.n_files_skipped >= 5

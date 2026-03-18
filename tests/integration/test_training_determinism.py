"""Integration test: training determinism — identical corpus produces identical corpus_hash (009 T015)."""

from __future__ import annotations

from pathlib import Path

from eigenhelm.training import train_eigenspace


class TestTrainingDeterminism:
    """Verify that training from the same corpus is deterministic."""

    def test_same_corpus_same_hash(self, corpus_dir: Path) -> None:
        """Training the same corpus twice produces identical corpus hashes."""
        result_a = train_eigenspace(corpus_dir, language="python", corpus_class="A")
        result_b = train_eigenspace(corpus_dir, language="python", corpus_class="A")

        assert result_a.model.corpus_hash == result_b.model.corpus_hash

    def test_same_corpus_same_components(self, corpus_dir: Path) -> None:
        """Deterministic PCA produces the same number of components."""
        result_a = train_eigenspace(corpus_dir, language="python", corpus_class="A")
        result_b = train_eigenspace(corpus_dir, language="python", corpus_class="A")

        assert result_a.model.n_components == result_b.model.n_components
        assert result_a.cumulative_variance == result_b.cumulative_variance

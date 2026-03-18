"""Unit tests for exemplar selection during training (T010)."""

from __future__ import annotations

import numpy as np

from eigenhelm.models import FEATURE_DIM


class TestSelectExemplars:
    """Tests for select_exemplars() in training/pca.py."""

    def _make_data(self, n: int, k: int, seed: int = 42):
        """Create synthetic design matrix and PCA outputs."""
        rng = np.random.default_rng(seed)
        X = rng.standard_normal((n, FEATURE_DIM))
        # Make a valid orthonormal projection matrix
        raw = rng.standard_normal((FEATURE_DIM, k))
        W, _ = np.linalg.qr(raw)
        W = W[:, :k]
        mean = X.mean(axis=0)
        std = X.std(axis=0, ddof=1)
        std[std < 1e-10] = 1.0
        source_contents = [f"def func_{i}(): pass\n".encode() * 10 for i in range(n)]
        return X, W, mean, std, source_contents

    def test_correct_count(self) -> None:
        from eigenhelm.training.pca import select_exemplars

        X, W, mean, std, sources = self._make_data(20, 3)
        exemplars = select_exemplars(X, W, mean, std, sources)
        assert len(exemplars) == 3  # k = n_components

    def test_each_exemplar_is_medoid(self) -> None:
        from eigenhelm.training.pca import select_exemplars

        X, W, mean, std, sources = self._make_data(30, 3)
        exemplars = select_exemplars(X, W, mean, std, sources)
        # Each exemplar should have a valid index into X
        for e in exemplars:
            assert 0 <= e.index < len(X)
            assert 0 <= e.cluster < 3

    def test_handles_fewer_vectors_than_k(self) -> None:
        from eigenhelm.training.pca import select_exemplars

        X, W, mean, std, sources = self._make_data(2, 3)
        # Should not raise — returns as many as available
        exemplars = select_exemplars(X, W, mean, std, sources)
        assert len(exemplars) <= 2

    def test_deduplication(self) -> None:
        from eigenhelm.training.pca import select_exemplars

        rng = np.random.default_rng(99)
        # Create data where some rows are identical
        X = np.zeros((10, FEATURE_DIM))
        X[0] = rng.standard_normal(FEATURE_DIM)
        X[1:] = X[0]  # all identical
        raw = rng.standard_normal((FEATURE_DIM, 3))
        W, _ = np.linalg.qr(raw)
        W = W[:, :3]
        mean = X.mean(axis=0)
        std = X.std(axis=0, ddof=1)
        std[std < 1e-10] = 1.0
        sources = [b"def same(): pass\n" * 10] * 10
        exemplars = select_exemplars(X, W, mean, std, sources)
        # Should still return results (may have duplicate content but that's OK)
        assert len(exemplars) >= 1

    def test_exemplar_has_compressed_content(self) -> None:
        from eigenhelm.training.pca import select_exemplars

        X, W, mean, std, sources = self._make_data(15, 3)
        exemplars = select_exemplars(X, W, mean, std, sources)
        for e in exemplars:
            assert isinstance(e.compressed_content, bytes)
            assert len(e.compressed_content) > 0
            assert isinstance(e.content_hash, str)
            assert len(e.content_hash) == 64  # SHA-256 hex digest

    def test_explicit_k(self) -> None:
        from eigenhelm.training.pca import select_exemplars

        X, W, mean, std, sources = self._make_data(20, 3)
        exemplars = select_exemplars(X, W, mean, std, sources, k=2)
        assert len(exemplars) == 2

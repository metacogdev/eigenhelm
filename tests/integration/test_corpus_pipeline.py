"""Integration tests: live corpus sync + eigenhelm-train pipeline.

These tests require a live network connection and download ~500 Python files.
They are skipped in normal CI:

    pytest -m "not integration"

Run manually to validate the full manifest-to-model pipeline:

    pytest tests/integration/test_corpus_pipeline.py -v -m integration
"""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.mark.integration
class TestCorpusSyncIntegration:
    """Live sync tests for corpora/lang-python.toml.

    SC-003: initial sync < 5 min on broadband; re-run < 2 seconds.
    SC-004: cumulative_variance >= 0.90 after training.
    """

    def test_sync_lang_python(self, tmp_path: Path) -> None:
        """Sync the Class A Python manifest and verify materialized output."""
        from eigenhelm.corpus.manifest import load_manifest
        from eigenhelm.corpus.sync import sync_manifest

        manifest = load_manifest(Path("corpora/lang-python.toml"))
        result = sync_manifest(manifest, tmp_path)

        assert result.failed == [], f"Sync failures: {result.failed}"
        assert len(result.synced) > 0, "No targets were synced"
        py_files = list(tmp_path.rglob("*.py"))
        assert len(py_files) > 0, "No .py files found in output directory"

        # Each expected target should have a subdirectory
        for target in manifest.targets:
            target_dir = tmp_path / target.name
            assert target_dir.exists(), (
                f"Missing subdirectory for target '{target.name}'"
            )
            sentinel = target_dir / ".eigenhelm-sync"
            assert sentinel.exists(), f"Missing sentinel for target '{target.name}'"

    def test_sync_idempotent(self, tmp_path: Path) -> None:
        """Re-running sync skips all already-present targets (SC-003: < 2s)."""
        import time

        from eigenhelm.corpus.manifest import load_manifest
        from eigenhelm.corpus.sync import sync_manifest

        manifest = load_manifest(Path("corpora/lang-python.toml"))

        # First run — downloads everything
        result1 = sync_manifest(manifest, tmp_path)
        assert result1.failed == []

        # Second run — must skip everything and complete quickly
        t0 = time.perf_counter()
        result2 = sync_manifest(manifest, tmp_path)
        elapsed = time.perf_counter() - t0

        assert result2.synced == [], f"Unexpected re-downloads: {result2.synced}"
        assert len(result2.skipped) == len(manifest.targets)
        assert elapsed < 2.0, f"Idempotent re-run took {elapsed:.2f}s (limit: 2s)"

    def test_train_on_synced_corpus(self, tmp_path: Path) -> None:
        """Train lang-python eigenspace; assert unique corpus_hash and variance >= 0.90.

        This is SC-004: the trained model must have cumulative_variance >= 0.90.
        """
        from eigenhelm.corpus.manifest import load_manifest
        from eigenhelm.corpus.sync import sync_manifest
        from eigenhelm.training import train_eigenspace

        manifest = load_manifest(Path("corpora/lang-python.toml"))
        result = sync_manifest(manifest, tmp_path)
        assert result.failed == []

        training_result = train_eigenspace(corpus_dir=tmp_path)

        assert training_result.model.corpus_hash, "corpus_hash must be non-empty"
        assert training_result.cumulative_variance >= 0.90, (
            f"cumulative_variance {training_result.cumulative_variance:.3f} < 0.90"
        )

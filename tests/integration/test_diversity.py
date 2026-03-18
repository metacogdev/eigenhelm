"""Integration tests for corpus diversity analysis (014-polyglot-discrimination).

Tests diversity analysis on real corpus data to verify the module produces
meaningful results with actual eigenhelm feature vectors.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from eigenhelm.validation.diversity import (
    DiversitySummary,
    render_human,
    render_json,
    run_diversity_analysis,
)


def _extract_design_matrix(
    corpus_dir: Path,
    language: str,
) -> tuple[np.ndarray, list[str]]:
    """Extract feature vectors and repo labels from a synced corpus.

    Returns (X, repo_labels) where X is (N, 69) and repo_labels has length N.
    """
    from eigenhelm.training.corpus import EXTENSION_TO_LANGUAGE
    from eigenhelm.virtue_extractor import VirtueExtractor

    extractor = VirtueExtractor()
    vectors: list[np.ndarray] = []
    labels: list[str] = []

    ext_map = {v: k for k, v in EXTENSION_TO_LANGUAGE.items()}
    target_ext = ext_map.get(language)
    if target_ext is None:
        return np.empty((0, 69)), []

    for repo_dir in sorted(corpus_dir.iterdir()):
        if not repo_dir.is_dir():
            continue
        repo_name = repo_dir.name
        for f in sorted(repo_dir.rglob(f"*{target_ext}")):
            if not f.is_file():
                continue
            source = f.read_text(encoding="utf-8", errors="replace")
            try:
                fvs = extractor.extract(source, language)
            except Exception:
                continue
            for fv in fvs:
                vectors.append(fv.values)
                labels.append(repo_name)

    if not vectors:
        return np.empty((0, 69)), []
    return np.vstack(vectors), labels


@pytest.fixture(scope="module")
def go_corpus_data() -> tuple[np.ndarray, list[str]]:
    """Extract Go corpus design matrix (cached per module)."""
    corpus_dir = Path("corpus/lang-go")
    if not corpus_dir.exists():
        pytest.skip("Go corpus not synced")
    X, labels = _extract_design_matrix(corpus_dir, "go")
    if X.shape[0] == 0:
        pytest.skip("No Go vectors extracted")
    return X, labels


@pytest.fixture(scope="module")
def js_corpus_data() -> tuple[np.ndarray, list[str]]:
    """Extract JavaScript corpus design matrix."""
    corpus_dir = Path("corpus/lang-javascript")
    if not corpus_dir.exists():
        pytest.skip("JS corpus not synced")
    X, labels = _extract_design_matrix(corpus_dir, "javascript")
    if X.shape[0] == 0:
        pytest.skip("No JS vectors extracted")
    return X, labels


class TestGoDiversityAnalysis:
    """Diversity analysis on the post-fix Go corpus (bbolt+chi+bubbletea+gjson)."""

    def test_go_diversity_passes(
        self, go_corpus_data: tuple[np.ndarray, list[str]]
    ) -> None:
        X, labels = go_corpus_data
        report = run_diversity_analysis(X, labels, "go")
        assert report.language == "go"
        assert report.n_features == 69
        assert report.n_repos >= 3
        # Post-fix Go corpus should pass diversity check
        assert report.passed, f"Go diversity failed: {report.warnings}"

    def test_go_has_multiple_repos(
        self, go_corpus_data: tuple[np.ndarray, list[str]]
    ) -> None:
        X, labels = go_corpus_data
        report = run_diversity_analysis(X, labels, "go")
        assert report.n_repos >= 3
        assert len(report.repo_stats) >= 3

    def test_go_effective_rank(
        self, go_corpus_data: tuple[np.ndarray, list[str]]
    ) -> None:
        X, labels = go_corpus_data
        report = run_diversity_analysis(X, labels, "go")
        assert report.effective_rank >= 3.0


class TestJavaScriptDiversityAnalysis:
    """Diversity analysis on the updated JS corpus."""

    def test_js_diversity_passes(
        self, js_corpus_data: tuple[np.ndarray, list[str]]
    ) -> None:
        X, labels = js_corpus_data
        report = run_diversity_analysis(X, labels, "javascript")
        assert report.language == "javascript"
        assert report.n_repos >= 3
        assert report.passed, f"JS diversity failed: {report.warnings}"


class TestSyntheticDiversity:
    """Test with synthetic data for controlled scenarios."""

    def test_low_diversity_flagged(self) -> None:
        """Corpus with most features dead should fail."""
        rng = np.random.default_rng(42)
        # Only 2 features have variance, rest are constant → dead_features > 10
        X = np.ones((40, 69))
        X[:, 0] = rng.standard_normal(40)
        X[:, 1] = rng.standard_normal(40)
        labels = ["repo_a"] * 20 + ["repo_b"] * 20
        report = run_diversity_analysis(X, labels, "synthetic_low")
        assert report.passed is False
        assert len(report.warnings) > 0

    def test_high_diversity_passes(self) -> None:
        """Corpus with well-separated repos across multiple dims should pass."""
        rng = np.random.default_rng(42)
        # Use random offsets across different dimensions for each repo
        # to ensure effective_rank > 3.0 (variance spread across dims)
        offset_a = rng.standard_normal(69) * 3
        offset_b = rng.standard_normal(69) * 3
        offset_c = rng.standard_normal(69) * 3
        X = np.vstack([
            rng.standard_normal((25, 69)) + offset_a,
            rng.standard_normal((25, 69)) + offset_b,
            rng.standard_normal((25, 69)) + offset_c,
        ])
        labels = ["repo_a"] * 25 + ["repo_b"] * 25 + ["repo_c"] * 25
        report = run_diversity_analysis(X, labels, "synthetic_high")
        assert report.passed is True


class TestSummaryAndRendering:
    """Test summary building and rendering with real corpus data."""

    def test_render_human_complete(
        self, go_corpus_data: tuple[np.ndarray, list[str]]
    ) -> None:
        X, labels = go_corpus_data
        report = run_diversity_analysis(X, labels, "go")
        summary = DiversitySummary(reports=(report,))
        output = render_human(summary)
        assert "go" in output
        assert "Corpus Diversity Report" in output

    def test_render_json_roundtrip(
        self, go_corpus_data: tuple[np.ndarray, list[str]]
    ) -> None:
        import json

        X, labels = go_corpus_data
        report = run_diversity_analysis(X, labels, "go")
        summary = DiversitySummary(reports=(report,))
        output = render_json(summary)
        data = json.loads(output)
        assert data["version"] == "014-polyglot-discrimination"
        assert "go" in data["languages"]

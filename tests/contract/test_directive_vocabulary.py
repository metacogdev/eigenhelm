"""Contract tests for the directive vocabulary (017-score-attribution).

Covers:
  T022 — Vocabulary invariants: membership, format, size, immutability.
"""

from __future__ import annotations

import re


from eigenhelm.attribution.constants import DIRECTIVE_VOCABULARY
from eigenhelm.attribution.directives import generate_directives
from eigenhelm.attribution.models import (
    DimensionAttribution,
    DirectAttribution,
    FeatureContribution,
    SourceLocation,
)

_LOC = SourceLocation(code_unit_name="f", start_line=1, end_line=5, file_path="f.py")

_SNAKE_CASE = re.compile(r"^[a-z][a-z0-9]*(_[a-z0-9]+)*$")


# ---------------------------------------------------------------------------
# (a) All generated categories are in DIRECTIVE_VOCABULARY
# ---------------------------------------------------------------------------


def test_generated_categories_in_vocabulary() -> None:
    """Every directive produced by generate_directives uses a known category."""
    dims: list[DimensionAttribution] = []

    # PCA dims — halstead (reduce_complexity)
    dims.append(
        DimensionAttribution(
            dimension="manifold_drift",
            normalized_score=0.8,
            available=True,
            method="pca",
            source_location=_LOC,
            features=(
                FeatureContribution(
                    feature_index=0,
                    feature_name="halstead_volume",
                    contribution_value=0.9,
                    contribution_magnitude=0.9,
                    raw_value=5.0,
                    corpus_mean=3.0,
                    standardized_deviation=2.0,
                    rank=1,
                ),
            ),
        )
    )
    # PCA dims — wl_hash positive (extract_repeated_logic)
    dims.append(
        DimensionAttribution(
            dimension="manifold_alignment",
            normalized_score=0.8,
            available=True,
            method="pca",
            source_location=_LOC,
            features=(
                FeatureContribution(
                    feature_index=10,
                    feature_name="wl_hash_bin_05",
                    contribution_value=0.9,
                    contribution_magnitude=0.9,
                    raw_value=5.0,
                    corpus_mean=3.0,
                    standardized_deviation=2.0,
                    rank=1,
                ),
            ),
        )
    )
    # PCA dims — wl_hash negative (review_structure)
    dims.append(
        DimensionAttribution(
            dimension="manifold_drift",
            normalized_score=0.8,
            available=True,
            method="pca",
            source_location=_LOC,
            features=(
                FeatureContribution(
                    feature_index=10,
                    feature_name="wl_hash_bin_05",
                    contribution_value=0.9,
                    contribution_magnitude=0.9,
                    raw_value=5.0,
                    corpus_mean=3.0,
                    standardized_deviation=-1.0,
                    rank=1,
                ),
            ),
        )
    )
    # Direct dims
    for metric in ("token_entropy", "compression_structure", "ncd_exemplar_distance"):
        dims.append(
            DimensionAttribution(
                dimension=metric,
                normalized_score=0.8,
                available=True,
                method="direct",
                source_location=_LOC,
                direct=DirectAttribution(
                    metric_name=metric,
                    computed_value=0.5,
                    normalization="linear",
                    normalized_score=0.8,
                ),
            )
        )

    directives = generate_directives(tuple(dims), threshold=0.3)
    categories = {d.category for d in directives}
    assert categories <= DIRECTIVE_VOCABULARY, (
        f"Unknown categories: {categories - DIRECTIVE_VOCABULARY}"
    )


# ---------------------------------------------------------------------------
# (b) All vocabulary entries are snake_case strings
# ---------------------------------------------------------------------------


def test_vocabulary_entries_snake_case() -> None:
    for entry in DIRECTIVE_VOCABULARY:
        assert isinstance(entry, str)
        assert _SNAKE_CASE.match(entry), f"{entry!r} is not snake_case"


# ---------------------------------------------------------------------------
# (c) Vocabulary has exactly 5 entries
# ---------------------------------------------------------------------------


def test_vocabulary_size() -> None:
    assert len(DIRECTIVE_VOCABULARY) == 5


# ---------------------------------------------------------------------------
# (d) DIRECTIVE_VOCABULARY is a frozenset (immutable)
# ---------------------------------------------------------------------------


def test_vocabulary_is_frozenset() -> None:
    assert isinstance(DIRECTIVE_VOCABULARY, frozenset)

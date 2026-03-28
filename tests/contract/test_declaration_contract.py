"""Contract tests for the declaration detection API.

Validates interface guarantees of detect_declarations() and analyze_declarations():
- Sorted, non-overlapping regions
- Empty results for unsupported/empty/whitespace inputs
- DeclarationRegion invariants (line ordering, count bounds)
- DeclarationAnalysis ratio and is_dominant semantics
"""

from __future__ import annotations

from eigenhelm.declarations import (
    DeclarationRegion,
    analyze_declarations,
    detect_declarations,
)

# ---------------------------------------------------------------------------
# Fixture: declaration-heavy Python source (multiple dataclasses)
# ---------------------------------------------------------------------------

_MULTI_DATACLASS_SOURCE = """\
from dataclasses import dataclass


@dataclass(frozen=True)
class Point:
    x: float
    y: float
    z: float


@dataclass(frozen=True)
class Color:
    r: int
    g: int
    b: int
    a: int


@dataclass(frozen=True)
class Vertex:
    position: Point
    color: Color
"""

# A source where declarations are a minority of lines
_LOGIC_HEAVY_SOURCE = """\
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    threshold: float


def compute(cfg: Config, values: list[float]) -> float:
    total = 0.0
    for v in values:
        if v > cfg.threshold:
            total += v * 2
        else:
            total += v
    result = total / len(values) if values else 0.0
    return round(result, 4)


def validate(cfg: Config) -> bool:
    if cfg.threshold < 0:
        return False
    if cfg.threshold > 100:
        return False
    return True


def transform(values: list[float]) -> list[float]:
    out = []
    for v in values:
        out.append(v ** 2 + v + 1)
    return out
"""


# ---------------------------------------------------------------------------
# 1. detect_declarations: sorted non-overlapping for multi-dataclass Python
# ---------------------------------------------------------------------------


def test_detect_returns_sorted_nonoverlapping_for_multiple_dataclasses():
    regions = detect_declarations(_MULTI_DATACLASS_SOURCE, "python")
    assert len(regions) >= 2, f"Expected multiple regions, got {len(regions)}"
    assert isinstance(regions, tuple)
    # Sorted by start_line
    for i in range(len(regions) - 1):
        assert regions[i].start_line < regions[i + 1].start_line
    # Non-overlapping
    _assert_no_overlaps(regions)


# ---------------------------------------------------------------------------
# 2. detect_declarations: empty for unsupported language
# ---------------------------------------------------------------------------


def test_detect_returns_empty_for_unsupported_language():
    result = detect_declarations("struct Foo { let x: Int }", "swift")
    assert result == ()


# ---------------------------------------------------------------------------
# 3. detect_declarations: empty for empty source
# ---------------------------------------------------------------------------


def test_detect_returns_empty_for_empty_source():
    result = detect_declarations("", "python")
    assert result == ()


# ---------------------------------------------------------------------------
# 4. detect_declarations: empty for whitespace-only source
# ---------------------------------------------------------------------------


def test_detect_returns_empty_for_whitespace_only_source():
    result = detect_declarations("   \n  ", "python")
    assert result == ()


# ---------------------------------------------------------------------------
# 5. analyze_declarations: correct ratio for declaration-heavy file
# ---------------------------------------------------------------------------


def test_analyze_computes_ratio_for_declaration_heavy_file():
    analysis = analyze_declarations(_MULTI_DATACLASS_SOURCE, "python")
    # This source is almost entirely declarations; ratio should be high
    assert analysis.ratio > 0.5, f"Expected high ratio, got {analysis.ratio}"
    assert analysis.declaration_lines > 0
    assert analysis.non_blank_non_comment_lines > 0
    assert analysis.declaration_lines <= analysis.non_blank_non_comment_lines


# ---------------------------------------------------------------------------
# 6. analyze_declarations: is_dominant=True when ratio >= 0.6
# ---------------------------------------------------------------------------


def test_analyze_is_dominant_true_when_ratio_high():
    analysis = analyze_declarations(_MULTI_DATACLASS_SOURCE, "python")
    # The multi-dataclass source should be declaration-dominant
    assert analysis.ratio >= 0.6, (
        f"Precondition: expected ratio >= 0.6, got {analysis.ratio}"
    )
    assert analysis.is_dominant is True


# ---------------------------------------------------------------------------
# 7. analyze_declarations: is_dominant=False when ratio < 0.6
# ---------------------------------------------------------------------------


def test_analyze_is_dominant_false_when_ratio_low():
    analysis = analyze_declarations(_LOGIC_HEAVY_SOURCE, "python")
    assert analysis.ratio < 0.6, (
        f"Precondition: expected ratio < 0.6, got {analysis.ratio}"
    )
    assert analysis.is_dominant is False


# ---------------------------------------------------------------------------
# 8. analyze_declarations: ratio=0.0 for empty source
# ---------------------------------------------------------------------------


def test_analyze_returns_zero_ratio_for_empty_source():
    analysis = analyze_declarations("", "python")
    assert analysis.ratio == 0.0
    assert analysis.regions == ()
    assert analysis.declaration_lines == 0
    assert analysis.is_dominant is False


# ---------------------------------------------------------------------------
# 9. All regions have start_line <= end_line
# ---------------------------------------------------------------------------


def test_all_regions_have_valid_line_ordering():
    regions = detect_declarations(_MULTI_DATACLASS_SOURCE, "python")
    assert len(regions) > 0, "Precondition: need regions to test"
    for r in regions:
        assert r.start_line <= r.end_line, (
            f"start_line ({r.start_line}) > end_line ({r.end_line}) for {r.node_name}"
        )


# ---------------------------------------------------------------------------
# 10. All regions have declaration_line_count >= 1 and <= span
# ---------------------------------------------------------------------------


def test_all_regions_have_valid_declaration_line_count():
    regions = detect_declarations(_MULTI_DATACLASS_SOURCE, "python")
    assert len(regions) > 0, "Precondition: need regions to test"
    for r in regions:
        span = r.end_line - r.start_line + 1
        assert r.declaration_line_count >= 1, (
            f"declaration_line_count < 1 for {r.node_name}"
        )
        assert r.declaration_line_count <= span, (
            f"declaration_line_count ({r.declaration_line_count}) > span ({span}) "
            f"for {r.node_name}"
        )


# ---------------------------------------------------------------------------
# 11. Regions are sorted by start_line
# ---------------------------------------------------------------------------


def test_regions_sorted_by_start_line():
    regions = detect_declarations(_MULTI_DATACLASS_SOURCE, "python")
    assert len(regions) >= 2, "Precondition: need multiple regions to test sorting"
    start_lines = [r.start_line for r in regions]
    assert start_lines == sorted(start_lines), (
        f"Regions not sorted by start_line: {start_lines}"
    )


# ---------------------------------------------------------------------------
# 12. Regions do not overlap
# ---------------------------------------------------------------------------


def test_regions_do_not_overlap():
    regions = detect_declarations(_MULTI_DATACLASS_SOURCE, "python")
    assert len(regions) >= 2, "Precondition: need multiple regions to test overlap"
    _assert_no_overlaps(regions)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _assert_no_overlaps(regions: tuple[DeclarationRegion, ...]) -> None:
    """Assert that regions are sorted and non-overlapping."""
    for i in range(len(regions) - 1):
        assert regions[i].end_line < regions[i + 1].start_line, (
            f"Overlapping regions: {regions[i].node_name} "
            f"(ends {regions[i].end_line}) and {regions[i + 1].node_name} "
            f"(starts {regions[i + 1].start_line})"
        )

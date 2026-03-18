"""Unit tests for scorecard module (T039)."""

from __future__ import annotations

from eigenhelm.critic import AestheticMetrics, AestheticScore, Critique, Violation
from eigenhelm.critic.anti_patterns import AntiPatternViolation
from eigenhelm.scoring.scorecard import (
    build_entry,
    build_scorecard,
    build_summary,
    render_human,
    render_json,
)


def _make_critique(
    *,
    entropy: float = 4.5,
    compression_ratio: float = 0.6,
    birkhoff_measure: float = 0.9,
    score_value: float = 0.3,
    violations: list[Violation] | None = None,
    anti_patterns: list[AntiPatternViolation] | None = None,
) -> Critique:
    """Create a Critique with controllable fields."""
    return Critique(
        score=AestheticScore(
            value=score_value,
            structural_confidence="low",
            weights={"shannon_entropy": 0.5, "birkhoff_measure": 0.5},
        ),
        quality_assessment="accept",
        violations=violations or [],
        metrics=AestheticMetrics(
            entropy=entropy,
            compression_ratio=compression_ratio,
            birkhoff_measure=birkhoff_measure,
            raw_bytes=500,
            compressed_bytes=300,
        ),
        anti_patterns=anti_patterns or [],
    )


class TestMandatoryChecks:
    """Tests for M1-M5 mandatory checks."""

    def test_m1_birkhoff_pass(self) -> None:
        entry = build_entry("test.py", _make_critique(birkhoff_measure=0.9))
        assert entry.mandatory_checks["M1_birkhoff"] is True

    def test_m1_birkhoff_fail(self) -> None:
        entry = build_entry("test.py", _make_critique(birkhoff_measure=0.5))
        assert entry.mandatory_checks["M1_birkhoff"] is False

    def test_m3_compression_pass(self) -> None:
        entry = build_entry("test.py", _make_critique(compression_ratio=0.6))
        assert entry.mandatory_checks["M3_compression_ratio"] is True

    def test_m3_compression_fail(self) -> None:
        entry = build_entry("test.py", _make_critique(compression_ratio=0.9))
        assert entry.mandatory_checks["M3_compression_ratio"] is False

    def test_m4_entropy_pass(self) -> None:
        entry = build_entry("test.py", _make_critique(entropy=4.5))
        assert entry.mandatory_checks["M4_shannon_entropy"] is True

    def test_m4_entropy_fail_low(self) -> None:
        entry = build_entry("test.py", _make_critique(entropy=2.0))
        assert entry.mandatory_checks["M4_shannon_entropy"] is False

    def test_m4_entropy_fail_high(self) -> None:
        entry = build_entry("test.py", _make_critique(entropy=7.5))
        assert entry.mandatory_checks["M4_shannon_entropy"] is False

    def test_m2_compression_structure_fallback_high_birkhoff_fails(self) -> None:
        # With no violations, M2 uses fallback: birkhoff directly (013 polarity).
        # birkhoff=0.9 → compression_structure=0.9 → 0.9 < 0.5 is False → FAIL
        entry = build_entry("test.py", _make_critique(birkhoff_measure=0.9, violations=[]))
        assert entry.mandatory_checks["M2_compression_structure"] is False

    def test_m2_compression_structure_fallback_low_birkhoff_passes(self) -> None:
        # birkhoff=0.3 → compression_structure=0.3 → 0.3 < 0.5 is True → PASS
        entry = build_entry("test.py", _make_critique(birkhoff_measure=0.3, violations=[]))
        assert entry.mandatory_checks["M2_compression_structure"] is True

    def test_m5_ncd_missing_from_topn_but_active_uses_contribution(self) -> None:
        # NCD is active (weight > 0) but absent from top-N violations.
        # Should derive value from contributions, not default to pass.
        critique = Critique(
            score=AestheticScore(
                value=0.4,
                structural_confidence="low",
                weights={
                    "token_entropy": 0.30,
                    "compression_structure": 0.30,
                    "ncd_exemplar_distance": 0.40,
                },
                contributions={
                    "token_entropy": 0.12,
                    "compression_structure": 0.12,
                    "ncd_exemplar_distance": 0.28,  # 0.28 / 0.40 = 0.70 raw NCD
                },
            ),
            quality_assessment="marginal",
            violations=[],  # NCD not in top-N
            metrics=AestheticMetrics(
                entropy=4.0, compression_ratio=0.6, birkhoff_measure=0.4,
                raw_bytes=500, compressed_bytes=300,
            ),
        )
        entry = build_entry("test.py", critique)
        # NCD raw = 0.70, threshold < 0.5 → should FAIL
        assert entry.mandatory_checks["M5_ncd_exemplar"] is False

    def test_m5_ncd_not_active_defaults_to_pass(self) -> None:
        # NCD weight is 0 (no exemplars) → genuinely unavailable → pass by default.
        entry = build_entry("test.py", _make_critique())
        assert entry.mandatory_checks["M5_ncd_exemplar"] is True

    def test_all_five_checks_present(self) -> None:
        entry = build_entry("test.py", _make_critique())
        assert len(entry.mandatory_checks) == 5
        assert all(k.startswith("M") for k in entry.mandatory_checks)


class TestQualitativeScores:
    """Tests for Q1-Q5 qualitative scores."""

    def test_q1_birkhoff_value(self) -> None:
        entry = build_entry("test.py", _make_critique(birkhoff_measure=0.85))
        assert abs(entry.qualitative_scores["Q1_birkhoff"] - 0.85) < 1e-6

    def test_q2_compression_structure(self) -> None:
        # Q2 = birkhoff_measure directly (013 polarity fix)
        entry = build_entry("test.py", _make_critique(birkhoff_measure=0.85))
        assert abs(entry.qualitative_scores["Q2_compression_structure"] - 0.85) < 1e-6

    def test_q3_normalized_entropy(self) -> None:
        # Q3 = 1.0 - entropy/8.0 (013 polarity fix); midpoint stays 0.5
        entry = build_entry("test.py", _make_critique(entropy=4.0))
        assert abs(entry.qualitative_scores["Q3_token_entropy"] - 0.5) < 1e-6

    def test_q5_overall(self) -> None:
        entry = build_entry("test.py", _make_critique(score_value=0.35))
        assert abs(entry.qualitative_scores["Q5_overall_aesthetic"] - 0.35) < 1e-6

    def test_all_five_scores_present(self) -> None:
        entry = build_entry("test.py", _make_critique())
        assert len(entry.qualitative_scores) == 5
        assert all(k.startswith("Q") for k in entry.qualitative_scores)


class TestSummary:
    """Tests for scorecard summary aggregation."""

    def test_pass_rates(self) -> None:
        entries = [
            build_entry("a.py", _make_critique(birkhoff_measure=0.9)),
            build_entry("b.py", _make_critique(birkhoff_measure=0.5)),
        ]
        summary = build_summary(entries)
        assert summary.mandatory_pass_rates["M1_birkhoff"] == 0.5

    def test_total_files(self) -> None:
        entries = [build_entry(f"{i}.py", _make_critique()) for i in range(5)]
        summary = build_summary(entries)
        assert summary.total_files == 5

    def test_qualitative_distributions(self) -> None:
        entries = [
            build_entry("a.py", _make_critique(birkhoff_measure=0.8)),
            build_entry("b.py", _make_critique(birkhoff_measure=1.0)),
        ]
        summary = build_summary(entries)
        q1 = summary.qualitative_distributions["Q1_birkhoff"]
        assert abs(q1["mean"] - 0.9) < 1e-6
        assert abs(q1["min"] - 0.8) < 1e-6
        assert abs(q1["max"] - 1.0) < 1e-6

    def test_anti_pattern_counts(self) -> None:
        ap = AntiPatternViolation(
            pattern_name="phantom_authorship",
            explanation="test",
            triggering_metrics={"volume": 3000.0},
        )
        entries = [
            build_entry("a.py", _make_critique(anti_patterns=[ap])),
            build_entry("b.py", _make_critique(anti_patterns=[ap])),
            build_entry("c.py", _make_critique()),
        ]
        summary = build_summary(entries)
        assert summary.anti_pattern_counts["phantom_authorship"] == 2


class TestScorecard:
    """Tests for full scorecard building."""

    def test_build_scorecard(self) -> None:
        file_critiques = [
            ("a.py", _make_critique()),
            ("b.py", _make_critique()),
        ]
        scorecard = build_scorecard(file_critiques)
        assert len(scorecard.entries) == 2
        assert scorecard.summary.total_files == 2


class TestRenderers:
    """Tests for scorecard rendering."""

    def test_human_readable(self) -> None:
        scorecard = build_scorecard([("test.py", _make_critique())])
        output = render_human(scorecard)
        assert "EIGENHELM SCORECARD" in output
        assert "test.py" in output

    def test_json_valid(self) -> None:
        import json

        scorecard = build_scorecard([("test.py", _make_critique())])
        output = render_json(scorecard)
        parsed = json.loads(output)
        assert "entries" in parsed
        assert "summary" in parsed
        assert parsed["entries"][0]["file_path"] == "test.py"

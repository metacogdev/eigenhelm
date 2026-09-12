"""Unit tests for attribution accuracy measurement (validation/attribution_audit.py)."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from eigenhelm.validation.attribution_audit import (
    AttributionAudit,
    AttributionPrecision,
    DirectiveRecord,
)


class TestDirectiveRecord:
    """DirectiveRecord is a frozen dataclass with the expected fields."""

    def test_fields(self) -> None:
        dr = DirectiveRecord(
            file_path="src/foo.py",
            directive_index=0,
            category="complexity",
            dimension="token_entropy",
            severity="high",
        )
        assert dr.file_path == "src/foo.py"
        assert dr.directive_index == 0
        assert dr.category == "complexity"
        assert dr.dimension == "token_entropy"
        assert dr.severity == "high"

    def test_frozen(self) -> None:
        dr = DirectiveRecord("a.py", 0, "cat", "dim", "low")
        with pytest.raises(AttributeError):
            dr.file_path = "other.py"  # type: ignore[misc]


class TestAttributionPrecision:
    """AttributionPrecision computes precision metrics correctly."""

    def test_precision_all_accurate(self) -> None:
        ap = AttributionPrecision(
            total=5, accurate=5, partial=0, inaccurate=0, unannotated=0
        )
        assert ap.precision == pytest.approx(1.0)
        assert ap.strict_precision == pytest.approx(1.0)

    def test_precision_mixed(self) -> None:
        ap = AttributionPrecision(
            total=10, accurate=3, partial=2, inaccurate=5, unannotated=0
        )
        # precision = (3 + 2) / (3 + 2 + 5) = 0.5
        assert ap.precision == pytest.approx(0.5)
        # strict = 3 / 10 = 0.3
        assert ap.strict_precision == pytest.approx(0.3)

    def test_precision_zero_annotated(self) -> None:
        ap = AttributionPrecision(
            total=5, accurate=0, partial=0, inaccurate=0, unannotated=5
        )
        assert ap.precision == pytest.approx(0.0)
        assert ap.strict_precision == pytest.approx(0.0)

    def test_precision_partial_only(self) -> None:
        ap = AttributionPrecision(
            total=4, accurate=0, partial=4, inaccurate=0, unannotated=0
        )
        assert ap.precision == pytest.approx(1.0)
        assert ap.strict_precision == pytest.approx(0.0)

    def test_frozen(self) -> None:
        ap = AttributionPrecision(
            total=1, accurate=1, partial=0, inaccurate=0, unannotated=0
        )
        with pytest.raises(AttributeError):
            ap.total = 99  # type: ignore[misc]


class TestCollectDirectives:
    """AttributionAudit.collect_directives extracts records from evaluations."""

    def test_empty_evaluations(self) -> None:
        audit = AttributionAudit()
        assert audit.collect_directives([]) == []

    def test_single_evaluation(self) -> None:
        ev = SimpleNamespace(
            file_path="src/main.py",
            directive_categories=["complexity", "naming"],
        )
        audit = AttributionAudit()
        records = audit.collect_directives([ev])
        assert len(records) == 2
        assert records[0].file_path == "src/main.py"
        assert records[0].directive_index == 0
        assert records[0].category == "complexity"
        assert records[1].directive_index == 1
        assert records[1].category == "naming"

    def test_multiple_evaluations(self) -> None:
        ev1 = SimpleNamespace(file_path="a.py", directive_categories=["cat1"])
        ev2 = SimpleNamespace(file_path="b.py", directive_categories=["cat2", "cat3"])
        audit = AttributionAudit()
        records = audit.collect_directives([ev1, ev2])
        assert len(records) == 3
        assert records[0].file_path == "a.py"
        assert records[1].file_path == "b.py"
        assert records[2].file_path == "b.py"

    def test_no_directives(self) -> None:
        ev = SimpleNamespace(file_path="empty.py", directive_categories=[])
        audit = AttributionAudit()
        records = audit.collect_directives([ev])
        assert records == []


class TestGenerateAnnotationTemplate:
    """AttributionAudit.generate_annotation_template writes JSON with null ratings."""

    def test_writes_json_template(self, tmp_path: Path) -> None:
        directives = [
            DirectiveRecord("a.py", 0, "complexity", "", ""),
            DirectiveRecord("b.py", 1, "naming", "", ""),
        ]
        output = tmp_path / "template.json"
        audit = AttributionAudit()
        audit.generate_annotation_template(directives, output)

        assert output.exists()
        data = json.loads(output.read_text())
        assert len(data) == 2
        assert data[0]["file_path"] == "a.py"
        assert data[0]["directive_index"] == 0
        assert data[0]["category"] == "complexity"
        assert data[0]["rating"] is None
        assert data[0]["rater"] is None
        assert data[1]["file_path"] == "b.py"

    def test_empty_directives(self, tmp_path: Path) -> None:
        output = tmp_path / "empty.json"
        audit = AttributionAudit()
        audit.generate_annotation_template([], output)
        data = json.loads(output.read_text())
        assert data == []


class TestLoadAnnotations:
    """AttributionAudit.load_annotations reads human ratings from JSON."""

    def test_load_single_rater(self, tmp_path: Path) -> None:
        data = [
            {"file_path": "a.py", "directive_index": 0, "rating": "accurate"},
            {"file_path": "b.py", "directive_index": 1, "rating": "inaccurate"},
        ]
        path = tmp_path / "annotations.json"
        path.write_text(json.dumps(data))

        audit = AttributionAudit()
        annotations = audit.load_annotations(path)
        assert annotations[("a.py", 0)] == ["accurate"]
        assert annotations[("b.py", 1)] == ["inaccurate"]

    def test_skips_null_ratings(self, tmp_path: Path) -> None:
        data = [
            {"file_path": "a.py", "directive_index": 0, "rating": None},
            {"file_path": "b.py", "directive_index": 1, "rating": "partial"},
        ]
        path = tmp_path / "annotations.json"
        path.write_text(json.dumps(data))

        audit = AttributionAudit()
        annotations = audit.load_annotations(path)
        assert ("a.py", 0) not in annotations
        assert annotations[("b.py", 1)] == ["partial"]

    def test_multiple_raters(self, tmp_path: Path) -> None:
        data = [
            {
                "file_path": "a.py",
                "directive_index": 0,
                "rating": "accurate",
                "rater": "r1",
            },
            {
                "file_path": "a.py",
                "directive_index": 0,
                "rating": "partial",
                "rater": "r2",
            },
        ]
        path = tmp_path / "annotations.json"
        path.write_text(json.dumps(data))

        audit = AttributionAudit()
        annotations = audit.load_annotations(path)
        assert annotations[("a.py", 0)] == ["accurate", "partial"]


class TestComputePrecision:
    """AttributionAudit.compute_precision aggregates annotations into precision metrics."""

    def test_all_accurate(self) -> None:
        directives = [
            DirectiveRecord("a.py", 0, "cat", "", ""),
            DirectiveRecord("a.py", 1, "cat", "", ""),
        ]
        annotations = {
            ("a.py", 0): ["accurate"],
            ("a.py", 1): ["accurate"],
        }
        audit = AttributionAudit()
        result = audit.compute_precision(directives, annotations)
        assert result.total == 2
        assert result.accurate == 2
        assert result.partial == 0
        assert result.inaccurate == 0
        assert result.unannotated == 0
        assert result.precision == pytest.approx(1.0)

    def test_unannotated_directives(self) -> None:
        directives = [
            DirectiveRecord("a.py", 0, "cat", "", ""),
            DirectiveRecord("b.py", 0, "cat", "", ""),
        ]
        annotations = {("a.py", 0): ["accurate"]}
        audit = AttributionAudit()
        result = audit.compute_precision(directives, annotations)
        assert result.unannotated == 1
        assert result.accurate == 1

    def test_majority_vote(self) -> None:
        directives = [DirectiveRecord("a.py", 0, "cat", "", "")]
        annotations = {("a.py", 0): ["accurate", "partial", "accurate"]}
        audit = AttributionAudit()
        result = audit.compute_precision(directives, annotations)
        assert result.accurate == 1
        assert result.partial == 0

    def test_unknown_rating_counts_as_unannotated(self) -> None:
        directives = [DirectiveRecord("a.py", 0, "cat", "", "")]
        annotations = {("a.py", 0): ["bogus"]}
        audit = AttributionAudit()
        result = audit.compute_precision(directives, annotations)
        assert result.unannotated == 1

    def test_empty_directives(self) -> None:
        audit = AttributionAudit()
        result = audit.compute_precision([], {})
        assert result.total == 0
        assert result.precision == pytest.approx(0.0)


class TestInterRaterKappa:
    """AttributionAudit.compute_inter_rater_kappa for Cohen's kappa."""

    def test_perfect_agreement(self) -> None:
        annotations = {(f"f{i}.py", 0): ["accurate", "accurate"] for i in range(5)}
        audit = AttributionAudit()
        kappa = audit.compute_inter_rater_kappa(annotations)
        assert kappa is not None
        assert kappa == pytest.approx(1.0)

    def test_insufficient_data_returns_none(self) -> None:
        annotations = {("a.py", 0): ["accurate", "accurate"]}  # only 1 pair, need 5
        audit = AttributionAudit()
        kappa = audit.compute_inter_rater_kappa(annotations)
        assert kappa is None

    def test_skips_non_paired(self) -> None:
        # 3 items with 2 ratings, 2 items with 1 rating => only 3 paired, < 5
        annotations = {
            ("a.py", 0): ["accurate", "accurate"],
            ("b.py", 0): ["partial", "partial"],
            ("c.py", 0): ["inaccurate", "accurate"],
            ("d.py", 0): ["accurate"],
            ("e.py", 0): ["partial"],
        }
        audit = AttributionAudit()
        kappa = audit.compute_inter_rater_kappa(annotations)
        assert kappa is None  # only 3 paired < 5

    def test_mixed_agreement(self) -> None:
        # 5 pairs with some disagreement
        annotations = {
            ("a.py", 0): ["accurate", "accurate"],
            ("b.py", 0): ["accurate", "partial"],  # both "positive" in binary
            ("c.py", 0): ["inaccurate", "inaccurate"],
            ("d.py", 0): ["accurate", "inaccurate"],  # disagree
            ("e.py", 0): ["partial", "partial"],
        }
        audit = AttributionAudit()
        kappa = audit.compute_inter_rater_kappa(annotations)
        assert kappa is not None
        # 4 agree (a,b,c,e), 1 disagrees (d) => kappa should be moderate
        assert -1.0 <= kappa <= 1.0

    def test_pe_equals_one_returns_one(self) -> None:
        # All same binary class from both raters => p_e = 1.0
        annotations = {(f"f{i}.py", 0): ["accurate", "partial"] for i in range(5)}
        # Both map to binary 1, so r1 = r2 = all 1s
        # p1_pos = 1.0, p2_pos = 1.0, p_e = 1.0*1.0 + 0*0 = 1.0
        audit = AttributionAudit()
        kappa = audit.compute_inter_rater_kappa(annotations)
        assert kappa == pytest.approx(1.0)

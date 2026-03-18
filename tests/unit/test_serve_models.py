"""Unit tests for all Pydantic models in eigenhelm.serve.models."""

from __future__ import annotations

import pytest
from eigenhelm.serve.models import (
    BatchRequest,
    BatchResponse,
    BatchSummary,
    EvaluateRequest,
    EvaluateResponse,
    FileEvalUnit,
    HealthResponse,
    ReadyResponse,
    ViolationOut,
)
from pydantic import ValidationError


class TestEvaluateRequest:
    def test_required_fields(self):
        with pytest.raises(ValidationError):
            EvaluateRequest()  # type: ignore[call-arg]

    def test_missing_source(self):
        with pytest.raises(ValidationError):
            EvaluateRequest(language="python")  # type: ignore[call-arg]

    def test_missing_language(self):
        with pytest.raises(ValidationError):
            EvaluateRequest(source="def f(): pass")  # type: ignore[call-arg]

    def test_valid(self):
        r = EvaluateRequest(source="def f(): pass", language="python")
        assert r.source == "def f(): pass"
        assert r.language == "python"
        assert r.file_path is None

    def test_with_file_path(self):
        r = EvaluateRequest(source="x", language="go", file_path="main.go")
        assert r.file_path == "main.go"


class TestViolationOut:
    def test_all_fields(self):
        v = ViolationOut(
            dimension="token_entropy",
            raw_value=3.8,
            normalized_value=0.47,
            contribution=0.31,
        )
        assert v.dimension == "token_entropy"
        assert v.raw_value == 3.8
        assert v.normalized_value == 0.47
        assert v.contribution == 0.31


class TestEvaluateResponse:
    def test_defaults(self):
        r = EvaluateResponse(
            decision="accept",
            score=0.22,
            structural_confidence="low",
            violations=[],
        )
        assert r.warning is None
        assert r.file_path is None

    def test_with_violations(self):
        v = ViolationOut(
            dimension="manifold_drift",
            raw_value=1.5,
            normalized_value=0.6,
            contribution=0.4,
        )
        r = EvaluateResponse(
            decision="warn",
            score=0.45,
            structural_confidence="high",
            violations=[v],
            warning=None,
            file_path="test.py",
        )
        assert len(r.violations) == 1
        assert r.violations[0].dimension == "manifold_drift"


class TestFileEvalUnit:
    def test_required_fields(self):
        with pytest.raises(ValidationError):
            FileEvalUnit()  # type: ignore[call-arg]

    def test_valid(self):
        f = FileEvalUnit(source="x = 1", language="python")
        assert f.file_path is None
        assert f.top_n == 3
        assert f.directive_threshold == 0.3

    def test_with_attribution_options(self):
        f = FileEvalUnit(
            source="x = 1",
            language="python",
            top_n=5,
            directive_threshold=0.6,
        )
        assert f.top_n == 5
        assert f.directive_threshold == 0.6

    def test_rejects_invalid_top_n(self):
        with pytest.raises(ValidationError):
            FileEvalUnit(source="x = 1", language="python", top_n=0)

    def test_rejects_invalid_directive_threshold(self):
        with pytest.raises(ValidationError):
            FileEvalUnit(source="x = 1", language="python", directive_threshold=1.1)


class TestBatchRequest:
    def test_empty_files_rejected(self):
        with pytest.raises(ValidationError):
            BatchRequest(files=[])

    def test_single_file(self):
        br = BatchRequest(files=[FileEvalUnit(source="x = 1", language="python")])
        assert len(br.files) == 1


class TestBatchSummary:
    def test_all_fields(self):
        s = BatchSummary(
            overall_decision="accept",
            total_files=3,
            accepted=3,
            warned=0,
            rejected=0,
            mean_score=0.2,
        )
        assert s.total_files == 3
        assert s.mean_score == 0.2


class TestBatchResponse:
    def test_structure(self):
        r = BatchResponse(
            results=[
                EvaluateResponse(
                    decision="accept",
                    score=0.2,
                    structural_confidence="low",
                    violations=[],
                )
            ],
            summary=BatchSummary(
                overall_decision="accept",
                total_files=1,
                accepted=1,
                warned=0,
                rejected=0,
                mean_score=0.2,
            ),
        )
        assert len(r.results) == 1
        assert r.summary.total_files == 1


class TestHealthResponse:
    def test_fields(self):
        h = HealthResponse(status="healthy", model_loaded=True)
        assert h.status == "healthy"
        assert h.model_loaded is True


class TestReadyResponse:
    def test_fields(self):
        r = ReadyResponse(status="ready", model_loaded=False)
        assert r.status == "ready"
        assert r.model_loaded is False

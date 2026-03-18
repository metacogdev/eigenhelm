"""Contract tests for agent integration HTTP API.

pytestmark = pytest.mark.contract
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.contract


# ---------------------------------------------------------------------------
# US5: Server Lifecycle
# ---------------------------------------------------------------------------


class TestServerLifecycle:
    """Invariant 13 and US5 health/ready contracts."""

    def test_create_app_constructs_without_error(self):
        """Invariant 13: create_app() with no args constructs without error or I/O."""
        from eigenhelm.serve import create_app

        app = create_app()
        assert app is not None

    def test_health_always_200(self, client):
        """GET /health always returns 200 with model_loaded bool."""
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert isinstance(data["model_loaded"], bool)

    def test_health_model_loaded_false_without_model(self, client):
        resp = client.get("/health")
        assert resp.json()["model_loaded"] is False

    def test_health_model_loaded_true_with_model(self, client_with_model):
        resp = client_with_model.get("/health")
        assert resp.json()["model_loaded"] is True

    def test_ready_200_without_model(self, client):
        """/ready returns 200 when no model is specified (immediate ready)."""
        resp = client.get("/ready")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ready"

    def test_ready_200_with_model(self, client_with_model):
        resp = client_with_model.get("/ready")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ready"
        assert resp.json()["model_loaded"] is True

    def test_health_content_type_json(self, client):
        """Invariant 9: Content-Type header must be application/json."""
        resp = client.get("/health")
        assert "application/json" in resp.headers["content-type"]

    def test_ready_content_type_json(self, client):
        resp = client.get("/ready")
        assert "application/json" in resp.headers["content-type"]

    def test_load_nonexistent_model_raises(self):
        """US5 scenario 5: loading a nonexistent model raises FileNotFoundError."""
        from eigenhelm.eigenspace import load_model

        with pytest.raises((FileNotFoundError, OSError)):
            load_model("nonexistent.npz")


# ---------------------------------------------------------------------------
# US1: POST /v1/evaluate
# ---------------------------------------------------------------------------


class TestEvaluateSingle:
    """Contract tests for POST /v1/evaluate."""

    def test_valid_response_shape(self, client):
        """Invariant 1: Valid response with required fields."""
        resp = client.post(
            "/v1/evaluate",
            json={"source": "def f(): pass", "language": "python"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["decision"] in {"accept", "warn", "reject"}
        assert 0.0 <= data["score"] <= 1.0
        assert data["structural_confidence"] in {"high", "low"}
        assert isinstance(data["violations"], list)

    def test_score_matches_direct_pipeline(self, client):
        """Invariant 2: HTTP score == direct DynamicHelm score."""
        from eigenhelm.helm import DynamicHelm, EvaluationRequest

        source = (
            "def quicksort(arr):\n"
            "    if len(arr) <= 1:\n"
            "        return arr\n"
            "    pivot = arr[0]\n"
            "    return quicksort([x for x in arr[1:] if x < pivot])"
            " + [pivot] + quicksort([x for x in arr[1:] if x >= pivot])"
        )
        resp = client.post(
            "/v1/evaluate",
            json={"source": source, "language": "python"},
        )
        api_score = resp.json()["score"]

        helm = DynamicHelm()
        direct = helm.evaluate(EvaluationRequest(source=source, language="python"))
        assert abs(api_score - direct.score) < 1e-10

    def test_empty_source_accepts(self, client):
        """Invariant 3: Empty source always returns accept with score 0.0."""
        resp = client.post(
            "/v1/evaluate",
            json={"source": "", "language": "python"},
        )
        data = resp.json()
        assert data["decision"] == "accept"
        assert data["score"] == 0.0

    def test_unsupported_language_degrades(self, client):
        """Invariant 4: Unsupported language → 200, low confidence, warning."""
        resp = client.post(
            "/v1/evaluate",
            json={"source": "some code", "language": "brainfuck"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["structural_confidence"] == "low"
        assert data["warning"] is not None

    def test_stateless_identical_results(self, client):
        """Invariant 12: Identical input → identical output."""
        payload = {"source": "x = 1\ny = 2\nz = x + y", "language": "python"}
        r1 = client.post("/v1/evaluate", json=payload).json()
        r2 = client.post("/v1/evaluate", json=payload).json()
        assert r1["score"] == r2["score"]
        assert r1["decision"] == r2["decision"]

    def test_content_type_json(self, client):
        """Invariant 9: Content-Type must be application/json."""
        resp = client.post(
            "/v1/evaluate",
            json={"source": "x = 1", "language": "python"},
        )
        assert "application/json" in resp.headers["content-type"]

    def test_422_on_missing_source(self, client):
        """Invariant 10: Missing required field → 422."""
        resp = client.post("/v1/evaluate", json={"language": "python"})
        assert resp.status_code == 422

    def test_422_on_missing_language(self, client):
        resp = client.post("/v1/evaluate", json={"source": "x = 1"})
        assert resp.status_code == 422

    def test_latency_budget(self, client, python_quicksort_source):
        """Invariant 11: < 200ms for 500 LoC input."""
        import time

        start = time.perf_counter()
        resp = client.post(
            "/v1/evaluate",
            json={"source": python_quicksort_source, "language": "python"},
        )
        elapsed = time.perf_counter() - start
        assert resp.status_code == 200
        assert elapsed < 0.200, f"Latency {elapsed:.3f}s exceeds 200ms budget"

    def test_file_path_echoed(self, client):
        """file_path from request is echoed in response."""
        resp = client.post(
            "/v1/evaluate",
            json={"source": "x = 1", "language": "python", "file_path": "test.py"},
        )
        assert resp.json()["file_path"] == "test.py"


# ---------------------------------------------------------------------------
# US2: POST /v1/evaluate/batch
# ---------------------------------------------------------------------------


class TestEvaluateBatch:
    """Contract tests for POST /v1/evaluate/batch."""

    def test_order_preserved(self, client):
        """Invariant 5: results[i] corresponds to files[i]."""
        files = [
            {"source": "x = 1", "language": "python", "file_path": "a.py"},
            {"source": "y = 2", "language": "python", "file_path": "b.py"},
            {"source": "z = 3", "language": "python", "file_path": "c.py"},
        ]
        resp = client.post("/v1/evaluate/batch", json={"files": files})
        assert resp.status_code == 200
        results = resp.json()["results"]
        for i, f in enumerate(files):
            assert results[i]["file_path"] == f["file_path"]

    def test_worst_of_reject(self, client):
        """Invariant 6: any reject → overall reject."""
        # Use empty source (accept) and very short repetitive code
        files = [
            {"source": "", "language": "python", "file_path": "good.py"},
            {"source": "x=1\n" * 100, "language": "python", "file_path": "bad.py"},
        ]
        resp = client.post("/v1/evaluate/batch", json={"files": files})
        data = resp.json()
        summary = data["summary"]
        # If any file is rejected, overall must be reject
        if summary["rejected"] > 0:
            assert summary["overall_decision"] == "reject"
        # If any warned but none rejected, overall must be warn
        elif summary["warned"] > 0:
            assert summary["overall_decision"] == "warn"
        else:
            assert summary["overall_decision"] == "accept"

    def test_counts_sum(self, client):
        """Invariant 7: accepted + warned + rejected == total_files."""
        files = [
            {"source": "x = 1", "language": "python"},
            {"source": "y = 2", "language": "python"},
        ]
        resp = client.post("/v1/evaluate/batch", json={"files": files})
        s = resp.json()["summary"]
        assert s["accepted"] + s["warned"] + s["rejected"] == s["total_files"]

    def test_mean_score_consistency(self, client):
        """Invariant 8: mean_score == arithmetic mean of result scores."""
        files = [
            {"source": "def f(): pass", "language": "python"},
            {"source": "def g(): return 1", "language": "python"},
            {"source": "", "language": "python"},
        ]
        resp = client.post("/v1/evaluate/batch", json={"files": files})
        data = resp.json()
        scores = [r["score"] for r in data["results"]]
        expected_mean = sum(scores) / len(scores)
        assert abs(data["summary"]["mean_score"] - expected_mean) < 1e-10

    def test_empty_files_422(self, client):
        """Empty files list returns 422."""
        resp = client.post("/v1/evaluate/batch", json={"files": []})
        assert resp.status_code == 422

    def test_mixed_language_batch(self, client):
        """Mixed-language batch completes without error."""
        files = [
            {"source": "def f(): pass", "language": "python"},
            {"source": "function f() {}", "language": "javascript"},
            {"source": "func main() {}", "language": "go"},
        ]
        resp = client.post("/v1/evaluate/batch", json={"files": files})
        assert resp.status_code == 200
        assert resp.json()["summary"]["total_files"] == 3

    def test_batch_accepts_attribution_options(self, client):
        """Batch entries can override attribution controls per file."""
        files = [
            {
                "source": "def f(x):\n    return x + 1\n",
                "language": "python",
                "file_path": "a.py",
                "top_n": 1,
                "directive_threshold": 0.9,
            },
            {
                "source": "def g(x):\n    return x * 2\n",
                "language": "python",
                "file_path": "b.py",
                "top_n": 5,
                "directive_threshold": 0.1,
            },
        ]
        resp = client.post("/v1/evaluate/batch", json={"files": files})
        assert resp.status_code == 200
        results = resp.json()["results"]
        assert results[0]["attribution"]["top_n"] == 1
        assert results[0]["attribution"]["directive_threshold"] == 0.9
        assert results[1]["attribution"]["top_n"] == 5
        assert results[1]["attribution"]["directive_threshold"] == 0.1

    def test_batch_sequential_order(self, client):
        """Invariant 14: Results maintain input order."""
        files = [
            {"source": f"x_{i} = {i}", "language": "python", "file_path": f"f{i}.py"}
            for i in range(5)
        ]
        resp = client.post("/v1/evaluate/batch", json={"files": files})
        results = resp.json()["results"]
        for i in range(5):
            assert results[i]["file_path"] == f"f{i}.py"

    def test_per_file_size_limit_413(self, client):
        """T046: Oversized file in batch returns 413."""
        from eigenhelm.serve import create_app
        from starlette.testclient import TestClient

        # Create app with very small per-file limit
        app = create_app(max_body_bytes=100)
        with TestClient(app) as small_client:
            files = [
                {"source": "x" * 200, "language": "python", "file_path": "big.py"},
            ]
            resp = small_client.post("/v1/evaluate/batch", json={"files": files})
            assert resp.status_code == 413
            assert resp.json()["error"] == "request_too_large"


# ---------------------------------------------------------------------------
# US4: Harness Contract Tests
# ---------------------------------------------------------------------------


class TestHarnessContracts:
    """Contract tests for the harness public interface."""

    def test_cli_api_score_parity(self, tmp_path):
        """Invariant 15: run_harness uses same pipeline as HTTP layer."""
        from eigenhelm.harness.runner import run_corpus
        from eigenhelm.helm import DynamicHelm, EvaluationRequest

        # Create a small corpus
        (tmp_path / "test.py").write_text("def f():\n    return 1\n")
        helm = DynamicHelm()
        stats = run_corpus(tmp_path, helm)

        # Direct call
        source = (tmp_path / "test.py").read_text()
        direct = helm.evaluate(EvaluationRequest(source=source, language="python"))
        assert abs(stats.scores[0] - direct.score) < 1e-10

    def test_harness_exit_code_empty_corpus(self, tmp_path):
        """Invariant 17: empty corpus → exit code 1."""
        from eigenhelm.cli.harness import main

        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        valid_dir = tmp_path / "valid"
        valid_dir.mkdir()
        (valid_dir / "test.py").write_text("x = 1\n")

        result = main(["--before", str(valid_dir), "--after", str(empty_dir)])
        assert result == 1

    def test_mann_whitney_significance(self, tmp_path):
        """Invariant 18: significant iff p_value < 0.05, improvement iff delta < 0."""
        from eigenhelm.harness.runner import run_harness

        # Create two distinct corpora with different score distributions
        before_dir = tmp_path / "before"
        before_dir.mkdir()
        after_dir = tmp_path / "after"
        after_dir.mkdir()

        # Before: complex code with higher aesthetic loss
        complex_code = (
            "def quicksort(arr):\n"
            "    if len(arr) <= 1:\n"
            "        return arr\n"
            "    pivot = arr[0]\n"
            "    left = [x for x in arr[1:] if x < pivot]\n"
            "    right = [x for x in arr[1:] if x >= pivot]\n"
            "    return quicksort(left) + [pivot] + quicksort(right)\n"
        )
        for i in range(10):
            (before_dir / f"complex_{i}.py").write_text(complex_code)

        # After: simple code with lower aesthetic loss
        for i in range(10):
            (after_dir / f"simple_{i}.py").write_text(f"x_{i} = 1\n" * 50)

        report = run_harness(before_dir, after_dir)
        # Verify invariant: significant iff p_value < 0.05
        assert report.significant == (report.p_value < 0.05)
        # Verify invariant: improvement iff significant and delta < 0
        assert report.improvement == (
            report.significant and report.delta_mean_score < 0.0
        )

    def test_cli_evaluate_exit_code_2_on_error(self, tmp_path):
        """Invariant 16: extraction failure → exit code 3 (runtime error).

        NOTE: Exit code semantics changed in feature 012-governance-surface:
          Old: 0=accept/warn, 1=reject, 2=runtime error
          New: 0=accept, 1=warn, 2=reject, 3=runtime error
        """
        from unittest.mock import patch

        from eigenhelm.cli.evaluate import main

        (tmp_path / "test.py").write_text("x = 1\n")

        with patch("eigenhelm.cli.evaluate.DynamicHelm") as mock_cls:
            mock_cls.return_value.evaluate.side_effect = RuntimeError("boom")
            result = main([str(tmp_path / "test.py")])
            assert result == 3

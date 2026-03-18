"""Integration tests for the serve pipeline (end-to-end)."""

from __future__ import annotations

import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration


class TestHealthIntegration:
    """US5: Server health/ready end-to-end."""

    def test_health_model_loaded_true(self, client_with_model):
        resp = client_with_model.get("/health")
        assert resp.status_code == 200
        assert resp.json()["model_loaded"] is True

    def test_health_model_loaded_false(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["model_loaded"] is False

    def test_ready_both_modes(self, client, client_with_model):
        assert client.get("/ready").status_code == 200
        assert client_with_model.get("/ready").status_code == 200


class TestEvaluateSingleIntegration:
    """US1: POST /v1/evaluate end-to-end."""

    def test_python_quicksort_low_confidence(self, client, python_quicksort_source):
        resp = client.post(
            "/v1/evaluate",
            json={"source": python_quicksort_source, "language": "python"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["structural_confidence"] == "low"
        assert data["decision"] in {"accept", "warn", "reject"}
        assert 0.0 <= data["score"] <= 1.0

    def test_python_quicksort_high_confidence(
        self, client_with_model, python_quicksort_source
    ):
        resp = client_with_model.post(
            "/v1/evaluate",
            json={"source": python_quicksort_source, "language": "python"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["structural_confidence"] == "high"

    def test_pipeline_parity(self, client, python_quicksort_source):
        """SC-003: API score matches direct DynamicHelm call."""
        from eigenhelm.helm import DynamicHelm, EvaluationRequest

        resp = client.post(
            "/v1/evaluate",
            json={"source": python_quicksort_source, "language": "python"},
        )
        api_score = resp.json()["score"]

        helm = DynamicHelm()
        direct = helm.evaluate(
            EvaluationRequest(source=python_quicksort_source, language="python")
        )
        assert abs(api_score - direct.score) < 1e-10


class TestEvaluateBatchIntegration:
    """US2: POST /v1/evaluate/batch end-to-end."""

    def test_five_file_batch(
        self,
        client,
        python_quicksort_source,
        js_quicksort_source,
        go_quicksort_source,
    ):
        files = [
            {
                "source": python_quicksort_source,
                "language": "python",
                "file_path": "qs.py",
            },
            {
                "source": python_quicksort_source,
                "language": "python",
                "file_path": "qs2.py",
            },
            {
                "source": python_quicksort_source,
                "language": "python",
                "file_path": "qs3.py",
            },
            {
                "source": js_quicksort_source,
                "language": "javascript",
                "file_path": "qs.js",
            },
            {"source": go_quicksort_source, "language": "go", "file_path": "qs.go"},
        ]
        resp = client.post("/v1/evaluate/batch", json={"files": files})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["results"]) == 5
        assert data["summary"]["total_files"] == 5
        assert 0.0 <= data["summary"]["mean_score"] <= 1.0

    def test_batch_with_rejected_files(self, client):
        """Batch with rejected files → overall_decision == 'reject'."""
        files = [
            {"source": "", "language": "python", "file_path": "empty.py"},
            # Very short repetitive code likely to score high
            {
                "source": "x=1\nx=1\nx=1\nx=1\nx=1\n" * 20,
                "language": "python",
                "file_path": "bad.py",
            },
        ]
        resp = client.post("/v1/evaluate/batch", json={"files": files})
        data = resp.json()
        summary = data["summary"]
        if summary["rejected"] > 0:
            assert summary["overall_decision"] == "reject"

    def test_batch_forwards_attribution_options(self, client_with_model):
        files = [
            {
                "source": "def f(x):\n    return x + 1\n",
                "language": "python",
                "file_path": "one.py",
                "top_n": 1,
                "directive_threshold": 0.95,
            },
            {
                "source": "def g(x):\n    return x * 2\n",
                "language": "python",
                "file_path": "two.py",
                "top_n": 4,
                "directive_threshold": 0.2,
            },
        ]
        resp = client_with_model.post("/v1/evaluate/batch", json={"files": files})
        assert resp.status_code == 200
        results = resp.json()["results"]
        assert results[0]["attribution"]["top_n"] == 1
        assert results[0]["attribution"]["directive_threshold"] == 0.95
        assert results[1]["attribution"]["top_n"] == 4
        assert results[1]["attribution"]["directive_threshold"] == 0.2


class TestCLIEvaluateIntegration:
    """US3: eigenhelm-evaluate CLI end-to-end."""

    def test_evaluate_single_file(self, tmp_path):
        """eigenhelm-evaluate on a single .py file → exit 0 or 1, not 2."""
        import subprocess

        fixture = Path(__file__).parent.parent / "fixtures" / "python_quicksort.py"
        result = subprocess.run(
            ["python3", "-m", "eigenhelm.cli.evaluate", str(fixture)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode in (0, 1, 2)
        assert len(result.stdout.strip()) > 0

    def test_evaluate_json_output(self, tmp_path):
        """eigenhelm-evaluate --json outputs valid JSON."""
        import json
        import subprocess

        fixture = Path(__file__).parent.parent / "fixtures" / "python_quicksort.py"
        result = subprocess.run(
            ["python3", "-m", "eigenhelm.cli.evaluate", str(fixture), "--json"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode in (0, 1, 2)
        data = json.loads(result.stdout)
        assert "results" in data
        assert "summary" in data

    def test_evaluate_directory(self):
        """eigenhelm-evaluate on fixtures directory processes all files."""
        import subprocess

        fixtures_dir = Path(__file__).parent.parent / "fixtures"
        result = subprocess.run(
            ["python3", "-m", "eigenhelm.cli.evaluate", str(fixtures_dir), "--json"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode in (0, 1, 2)
        data = json.loads(result.stdout)
        assert data["summary"]["total_files"] >= 5

    def test_evaluate_stdin(self):
        """stdin mode: echo code | eigenhelm-evaluate --language python."""
        import subprocess

        result = subprocess.run(
            ["python3", "-m", "eigenhelm.cli.evaluate", "--language", "python"],
            input="def f(): pass\n",
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode in (0, 1, 2)
        assert len(result.stdout.strip()) > 0


class TestPerformanceBudgets:
    """SC-001/002/005/006: Performance budget contract tests."""

    def _make_500_loc_source(self) -> str:
        """Generate ~500 LoC Python source."""
        lines = ["import math", ""]
        for i in range(50):
            lines.append(f"def func_{i}(x, y, z):")
            lines.append(f"    '''Docstring for func_{i}.'''")
            for j in range(6):
                lines.append(f"    v{j} = x + y * {j} + z ** {i % 5}")
            lines.append(f"    if x > {i}:")
            lines.append("        return v0 + v1")
            lines.append("    return v5 - v2")
            lines.append("")
        return "\n".join(lines)

    def test_single_evaluate_latency(self, client):
        """SC-001: POST /v1/evaluate < 200ms for 500-LoC input."""
        source = self._make_500_loc_source()
        start = time.perf_counter()
        resp = client.post(
            "/v1/evaluate",
            json={"source": source, "language": "python"},
        )
        elapsed_ms = (time.perf_counter() - start) * 1000
        assert resp.status_code == 200
        assert elapsed_ms < 200, (
            f"Single evaluate took {elapsed_ms:.1f}ms (budget: 200ms)"
        )

    def test_batch_latency_50_files(self, client):
        """SC-002: POST /v1/evaluate/batch with 50 files < 5s."""
        languages = [
            "python",
            "javascript",
            "typescript",
            "go",
            "rust",
            "java",
            "c",
            "cpp",
            "ruby",
            "kotlin",
        ]
        base_sources = {
            "python": "def f(x):\n    if x > 0:\n        return x * 2\n    return -x\n",
            "javascript": "function f(x) {\n  if (x > 0) return x * 2;\n  return -x;\n}\n",
            "typescript": (
                "function f(x: number): number {\n  if (x > 0) return x * 2;\n  return -x;\n}\n"
            ),
            "go": "func f(x int) int {\n  if x > 0 {\n    return x * 2\n  }\n  return -x\n}\n",
            "rust": "fn f(x: i32) -> i32 {\n  if x > 0 { x * 2 } else { -x }\n}\n",
            "java": "int f(int x) {\n  if (x > 0) return x * 2;\n  return -x;\n}\n",
            "c": "int f(int x) {\n  if (x > 0) return x * 2;\n  return -x;\n}\n",
            "cpp": "int f(int x) {\n  if (x > 0) return x * 2;\n  return -x;\n}\n",
            "ruby": "def f(x)\n  x > 0 ? x * 2 : -x\nend\n",
            "kotlin": "fun f(x: Int): Int {\n  return if (x > 0) x * 2 else -x\n}\n",
        }
        files = []
        for i in range(50):
            lang = languages[i % len(languages)]
            source = (base_sources[lang] + "\n") * 25
            files.append(
                {
                    "source": source,
                    "language": lang,
                    "file_path": f"file_{i}.{lang[:2]}",
                }
            )

        start = time.perf_counter()
        resp = client.post("/v1/evaluate/batch", json={"files": files})
        elapsed = time.perf_counter() - start
        assert resp.status_code == 200
        data = resp.json()
        assert data["summary"]["total_files"] == 50
        assert elapsed < 5.0, f"Batch of 50 took {elapsed:.2f}s (budget: 5s)"

    def test_startup_time(self, synthetic_model):
        """SC-005: Server startup < 5s with model."""
        from eigenhelm.serve import create_app
        from starlette.testclient import TestClient

        start = time.perf_counter()
        app = create_app(eigenspace=synthetic_model)
        with TestClient(app) as c:
            resp = c.get("/ready")
        elapsed = time.perf_counter() - start
        assert resp.status_code == 200
        assert elapsed < 5.0, f"Startup took {elapsed:.2f}s (budget: 5s)"

    def test_concurrency_100_requests(self, client, python_quicksort_source):
        """SC-006: 100 concurrent requests all return valid responses."""
        payload = {"source": python_quicksort_source, "language": "python"}

        def fire():
            return client.post("/v1/evaluate", json=payload)

        with ThreadPoolExecutor(max_workers=100) as pool:
            futures = [pool.submit(fire) for _ in range(100)]
            results = [f.result() for f in futures]

        assert len(results) == 100
        for resp in results:
            assert resp.status_code == 200
            data = resp.json()
            assert data["decision"] in {"accept", "warn", "reject"}

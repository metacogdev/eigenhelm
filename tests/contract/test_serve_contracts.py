"""Contract tests for the HTTP serve layer: middleware and routes.

Tests verify the user-facing contracts of the HTTP API:
- Size limit middleware (413 on oversized requests)
- Timeout middleware (504 on slow /v1/ routes, no timeout on health)
- Evaluate route contracts (single + batch)
- Health and readiness probe contracts
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.contract


# ---------------------------------------------------------------------------
# Size limit middleware
# ---------------------------------------------------------------------------


class TestSizeLimitMiddleware:
    """ContentSizeLimitMiddleware contract: reject oversized requests with 413."""

    def test_small_request_passes_through(self, client):
        resp = client.post(
            "/v1/evaluate",
            json={"source": "x = 1", "language": "python"},
        )
        # Should not be 413
        assert resp.status_code != 413

    def test_oversized_request_returns_413(self):
        """A request exceeding max_body_bytes gets 413."""
        from eigenhelm.serve import create_app
        from starlette.testclient import TestClient

        # Create app with tiny size limit
        app = create_app(max_batch_bytes=100)
        with TestClient(app) as c:
            resp = c.post(
                "/v1/evaluate",
                json={"source": "x" * 500, "language": "python"},
            )
            assert resp.status_code == 413
            body = resp.json()
            assert body["error"] == "request_too_large"

    def test_non_http_scope_passes_through(self):
        """Non-HTTP scopes (e.g., websocket) pass through unmodified."""
        import asyncio

        from eigenhelm.serve.middleware.size_limit import ContentSizeLimitMiddleware

        calls = []

        async def dummy_app(scope, receive, send):
            calls.append(scope["type"])

        middleware = ContentSizeLimitMiddleware(dummy_app, max_bytes=100)
        scope = {"type": "websocket"}

        asyncio.new_event_loop().run_until_complete(middleware(scope, None, None))
        assert calls == ["websocket"]


# ---------------------------------------------------------------------------
# Timeout middleware
# ---------------------------------------------------------------------------


class TestTimeoutMiddleware:
    """TimeoutMiddleware contract: timeout on /v1/ routes, skip health."""

    def test_health_not_subject_to_timeout(self):
        """GET /health is not wrapped in a timeout."""
        from eigenhelm.serve import create_app
        from starlette.testclient import TestClient

        app = create_app(timeout_seconds=0.001)
        with TestClient(app) as c:
            resp = c.get("/health")
            assert resp.status_code == 200

    def test_non_http_scope_passes_through(self):
        """Non-HTTP scopes pass through unmodified."""
        import asyncio

        from eigenhelm.serve.middleware.timeout import TimeoutMiddleware

        calls = []

        async def dummy_app(scope, receive, send):
            calls.append(scope["type"])

        middleware = TimeoutMiddleware(dummy_app, timeout_seconds=1.0)
        scope = {"type": "websocket"}

        asyncio.new_event_loop().run_until_complete(middleware(scope, None, None))
        assert calls == ["websocket"]

    def test_non_v1_path_not_subject_to_timeout(self):
        """Non-/v1/ HTTP paths bypass timeout."""
        import asyncio

        from eigenhelm.serve.middleware.timeout import TimeoutMiddleware

        calls = []

        async def dummy_app(scope, receive, send):
            calls.append("called")

        middleware = TimeoutMiddleware(dummy_app, timeout_seconds=0.001)
        scope = {"type": "http", "path": "/health"}

        asyncio.new_event_loop().run_until_complete(middleware(scope, None, None))
        assert calls == ["called"]

    def test_v1_timeout_returns_504(self):
        """Slow /v1/ routes get 504 Gateway Timeout."""
        import asyncio

        from eigenhelm.serve.middleware.timeout import TimeoutMiddleware

        async def slow_app(scope, receive, send):
            await asyncio.sleep(10)

        middleware = TimeoutMiddleware(slow_app, timeout_seconds=0.01)
        scope = {"type": "http", "path": "/v1/evaluate"}

        sent_messages = []

        async def mock_receive():
            return {"type": "http.request", "body": b""}

        async def mock_send(msg):
            sent_messages.append(msg)

        asyncio.new_event_loop().run_until_complete(
            middleware(scope, mock_receive, mock_send)
        )
        # Should send a 504 response
        assert len(sent_messages) == 2
        assert sent_messages[0]["type"] == "http.response.start"
        assert sent_messages[0]["status"] == 504
        import json

        body = json.loads(sent_messages[1]["body"])
        assert body["error"] == "evaluation_timeout"


# ---------------------------------------------------------------------------
# Health and readiness routes
# ---------------------------------------------------------------------------


class TestHealthRoutes:
    """GET /health and GET /ready contracts."""

    def test_health_returns_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "model_loaded" in data

    def test_health_model_loaded_false_without_model(self, client):
        resp = client.get("/health")
        data = resp.json()
        assert data["model_loaded"] is False

    def test_health_model_loaded_true_with_model(self, client_with_model):
        resp = client_with_model.get("/health")
        data = resp.json()
        assert data["model_loaded"] is True

    def test_ready_returns_200_when_ready(self, client):
        resp = client.get("/ready")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ready"

    def test_ready_returns_503_before_lifespan(self):
        """If helm is not set, /ready returns 503."""
        from fastapi import FastAPI
        from starlette.testclient import TestClient

        # Create a bare app without lifespan (simulating pre-startup)
        app = FastAPI()

        from eigenhelm.serve.routes.health import router

        app.include_router(router)

        # Don't set app.state._helm at all
        with TestClient(app, raise_server_exceptions=False) as c:
            resp = c.get("/ready")
            assert resp.status_code == 503
            data = resp.json()
            assert data["status"] == "starting"


# ---------------------------------------------------------------------------
# Evaluate route
# ---------------------------------------------------------------------------


class TestEvaluateRoute:
    """POST /v1/evaluate contract."""

    def test_evaluate_returns_200(self, client):
        resp = client.post(
            "/v1/evaluate",
            json={"source": "def hello(): pass", "language": "python"},
        )
        assert resp.status_code == 200

    def test_evaluate_response_fields(self, client):
        resp = client.post(
            "/v1/evaluate",
            json={"source": "def hello(): pass", "language": "python"},
        )
        data = resp.json()
        assert "decision" in data
        assert "score" in data
        assert "structural_confidence" in data
        assert "violations" in data
        assert data["decision"] in ("accept", "warn", "reject")

    def test_evaluate_with_file_path(self, client):
        resp = client.post(
            "/v1/evaluate",
            json={
                "source": "def hello(): pass",
                "language": "python",
                "file_path": "hello.py",
            },
        )
        data = resp.json()
        assert data.get("file_path") == "hello.py"

    def test_evaluate_contributions_present(self, client):
        resp = client.post(
            "/v1/evaluate",
            json={"source": "def hello(): pass", "language": "python"},
        )
        data = resp.json()
        assert "contributions" in data
        assert isinstance(data["contributions"], list)

    def test_evaluate_missing_source_returns_422(self, client):
        resp = client.post(
            "/v1/evaluate",
            json={"language": "python"},
        )
        assert resp.status_code == 422

    def test_evaluate_missing_language_returns_422(self, client):
        resp = client.post(
            "/v1/evaluate",
            json={"source": "x = 1"},
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Batch evaluate route
# ---------------------------------------------------------------------------


class TestBatchEvaluateRoute:
    """POST /v1/evaluate/batch contract."""

    def test_batch_returns_200(self, client):
        resp = client.post(
            "/v1/evaluate/batch",
            json={
                "files": [
                    {"source": "def a(): pass", "language": "python"},
                    {"source": "def b(): return 1", "language": "python"},
                ]
            },
        )
        assert resp.status_code == 200

    def test_batch_response_structure(self, client):
        resp = client.post(
            "/v1/evaluate/batch",
            json={
                "files": [
                    {"source": "def a(): pass", "language": "python"},
                ]
            },
        )
        data = resp.json()
        assert "results" in data
        assert "summary" in data
        assert len(data["results"]) == 1
        summary = data["summary"]
        assert summary["total_files"] == 1
        assert summary["overall_decision"] in ("accept", "warn", "reject")
        assert "mean_score" in summary
        assert "accepted" in summary
        assert "warned" in summary
        assert "rejected" in summary

    def test_batch_per_file_size_limit_returns_413(self):
        """Batch validates per-file size against max_body_bytes."""
        from eigenhelm.serve import create_app
        from starlette.testclient import TestClient

        app = create_app(max_body_bytes=50)
        with TestClient(app) as c:
            resp = c.post(
                "/v1/evaluate/batch",
                json={
                    "files": [
                        {
                            "source": "x" * 200,
                            "language": "python",
                            "file_path": "big.py",
                        },
                    ]
                },
            )
            assert resp.status_code == 413
            body = resp.json()
            assert body["error"] == "request_too_large"
            assert "big.py" in body["detail"]

    def test_batch_empty_files_returns_422(self, client):
        """Empty files array violates min_length=1 on BatchRequest."""
        resp = client.post(
            "/v1/evaluate/batch",
            json={"files": []},
        )
        assert resp.status_code == 422

    def test_batch_summary_counts_add_up(self, client):
        resp = client.post(
            "/v1/evaluate/batch",
            json={
                "files": [
                    {"source": "def a(): pass", "language": "python"},
                    {"source": "def b(): return 1", "language": "python"},
                    {"source": "def c(): return None", "language": "python"},
                ]
            },
        )
        data = resp.json()
        summary = data["summary"]
        total = summary["accepted"] + summary["warned"] + summary["rejected"]
        assert total == summary["total_files"]
        assert total == 3


# ---------------------------------------------------------------------------
# Evaluate route: batch summary decision logic
# ---------------------------------------------------------------------------


class TestBatchSummaryDecision:
    """_compute_summary contract: overall decision follows reject > warn > accept."""

    def test_compute_summary_all_accept(self):
        from eigenhelm.serve.routes.evaluate import _compute_summary
        from eigenhelm.serve.models import EvaluateResponse

        results = [
            EvaluateResponse(
                decision="accept",
                score=0.8,
                structural_confidence="high",
                violations=[],
            ),
            EvaluateResponse(
                decision="accept",
                score=0.7,
                structural_confidence="high",
                violations=[],
            ),
        ]
        summary = _compute_summary(results)
        assert summary.overall_decision == "accept"
        assert summary.total_files == 2
        assert summary.accepted == 2
        assert summary.warned == 0
        assert summary.rejected == 0

    def test_compute_summary_warn_overrides_accept(self):
        from eigenhelm.serve.routes.evaluate import _compute_summary
        from eigenhelm.serve.models import EvaluateResponse

        results = [
            EvaluateResponse(
                decision="accept",
                score=0.8,
                structural_confidence="high",
                violations=[],
            ),
            EvaluateResponse(
                decision="warn", score=0.5, structural_confidence="high", violations=[]
            ),
        ]
        summary = _compute_summary(results)
        assert summary.overall_decision == "warn"

    def test_compute_summary_reject_overrides_all(self):
        from eigenhelm.serve.routes.evaluate import _compute_summary
        from eigenhelm.serve.models import EvaluateResponse

        results = [
            EvaluateResponse(
                decision="accept",
                score=0.8,
                structural_confidence="high",
                violations=[],
            ),
            EvaluateResponse(
                decision="warn", score=0.5, structural_confidence="high", violations=[]
            ),
            EvaluateResponse(
                decision="reject",
                score=0.2,
                structural_confidence="high",
                violations=[],
            ),
        ]
        summary = _compute_summary(results)
        assert summary.overall_decision == "reject"
        assert summary.rejected == 1

    def test_compute_summary_mean_score(self):
        from eigenhelm.serve.routes.evaluate import _compute_summary
        from eigenhelm.serve.models import EvaluateResponse

        results = [
            EvaluateResponse(
                decision="accept",
                score=0.6,
                structural_confidence="high",
                violations=[],
            ),
            EvaluateResponse(
                decision="accept",
                score=0.8,
                structural_confidence="high",
                violations=[],
            ),
        ]
        summary = _compute_summary(results)
        assert abs(summary.mean_score - 0.7) < 0.001

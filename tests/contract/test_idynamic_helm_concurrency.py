"""Contract tests for IDynamicHelm thread safety — invariant 18.

Invariant 18: concurrent evaluate() calls safe; concurrent steer() with
different sessions safe.
"""

from __future__ import annotations

import threading
from typing import Any

import pytest
from eigenhelm.helm import DynamicHelm, EvaluationRequest, SteeringRequest

PYTHON_SOURCE = """\
def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left  = [x for x in arr if x < pivot]
    mid   = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + mid + quicksort(right)
"""


@pytest.mark.contract
class TestConcurrency:
    def test_concurrent_evaluate_safe(self):
        """Multiple threads calling evaluate() on the same instance must not raise."""
        helm = DynamicHelm()
        req = EvaluationRequest(source=PYTHON_SOURCE, language="python")
        errors: list[Exception] = []
        results: list[Any] = []
        lock = threading.Lock()

        def run():
            try:
                r = helm.evaluate(req)
                with lock:
                    results.append(r)
            except Exception as e:
                with lock:
                    errors.append(e)

        threads = [threading.Thread(target=run) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == [], f"Concurrent evaluate() raised: {errors}"
        assert len(results) == 8

    def test_concurrent_evaluate_deterministic(self):
        """All concurrent evaluate() calls return the same score."""
        helm = DynamicHelm()
        req = EvaluationRequest(source=PYTHON_SOURCE, language="python")
        scores: list[float] = []
        lock = threading.Lock()

        def run():
            r = helm.evaluate(req)
            with lock:
                scores.append(r.score)

        threads = [threading.Thread(target=run) for _ in range(6)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(scores) == 6
        # All scores should be identical (determinism)
        assert all(abs(s - scores[0]) < 1e-9 for s in scores), (
            f"Non-deterministic concurrent results: {scores}"
        )

    def test_concurrent_steer_different_sessions_safe(self):
        """steer() with different sessions from multiple threads must not raise."""
        helm = DynamicHelm()
        errors: list[Exception] = []
        results: list[Any] = []
        lock = threading.Lock()

        def run():
            session = helm.create_session()
            req = SteeringRequest(
                source=PYTHON_SOURCE, language="python", tau=0.8, p=0.9, session=session
            )
            try:
                r = helm.steer(req)
                with lock:
                    results.append(r)
            except Exception as e:
                with lock:
                    errors.append(e)

        threads = [threading.Thread(target=run) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == [], f"Concurrent steer() raised: {errors}"
        assert len(results) == 8

    def test_create_session_is_independent(self):
        """Each create_session() returns an independent SteeringSession."""
        helm = DynamicHelm()
        s1 = helm.create_session()
        s2 = helm.create_session()
        s1.step = 5
        assert s2.step == 0, "Sessions should be independent"

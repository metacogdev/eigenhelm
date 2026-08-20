"""Concurrency regression tests for exemplar identity (issue 62).

The hazard: AestheticCritic previously stored exemplar bytes and identities
in two parallel mutable lists. ``evaluate()`` read each attribute separately,
so a state swap or in-place mutation between the two reads could pair the
wrong identity with the nearest exemplar — silently corrupting the
``nearest_exemplar_id`` reported on Critique.

These tests pin the new contract: bytes and identity travel together as one
immutable record, length mismatches fail at construction, and many threads
evaluating concurrently never observe a torn (distance, identity) pair.
"""

from __future__ import annotations

import hashlib
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

from eigenhelm.critic.aesthetic_critic import AestheticCritic
from eigenhelm.critic.exemplars import ExemplarBinding, bind_exemplars
from eigenhelm.critic.ncd import ncd_to_nearest_binding


def _make_exemplars(n: int = 8) -> tuple[list[bytes], list[str]]:
    """Return (bytes, ids) where ids are SHA-256 of the bytes."""
    bytes_list: list[bytes] = []
    ids: list[str] = []
    for i in range(n):
        # Each exemplar must be at least min_compression_bytes (50) for NCD.
        body = (f"def exemplar_{i}(x):\n    return x * {i}\n" * 6).encode("utf-8")
        bytes_list.append(body)
        ids.append(hashlib.sha256(body).hexdigest())
    return bytes_list, ids


class TestExemplarBindingValidatesAtConstruction:
    """Bind-time validation surfaces misconfiguration at the construction site,
    not on the first evaluate() call from a request handler."""

    def test_length_mismatch_raises_in_bind_exemplars(self) -> None:
        with pytest.raises(ValueError, match="same length"):
            bind_exemplars([b"a" * 100, b"b" * 100], ["only-one-id"])

    def test_length_mismatch_raises_in_critic_init(self) -> None:
        with pytest.raises(ValueError, match="same length"):
            AestheticCritic(
                exemplars=[b"a" * 100, b"b" * 100],
                exemplar_ids=["only-one-id"],
            )

    def test_none_exemplars_returns_none(self) -> None:
        assert bind_exemplars(None, None) is None
        assert bind_exemplars(None, ["ignored"]) is None

    def test_empty_exemplars_returns_empty_tuple(self) -> None:
        result = bind_exemplars([], [])
        assert result == ()

    def test_missing_ids_pads_with_empty_string(self) -> None:
        result = bind_exemplars([b"x" * 100, b"y" * 100], None)
        assert result is not None
        assert all(b.identity == "" for b in result)
        assert [b.content for b in result] == [b"x" * 100, b"y" * 100]


class TestExemplarBindingIsImmutable:
    """The bound tuple snapshots the input — later mutation cannot corrupt it."""

    def test_record_is_frozen(self) -> None:
        binding = ExemplarBinding(content=b"x" * 100, identity="abc")
        with pytest.raises(Exception):  # FrozenInstanceError
            binding.content = b"different"  # type: ignore[misc]
        with pytest.raises(Exception):
            binding.identity = "different"  # type: ignore[misc]

    def test_input_list_mutation_does_not_corrupt_binding(self) -> None:
        bytes_list, ids = _make_exemplars(3)
        critic = AestheticCritic(exemplars=bytes_list, exemplar_ids=ids)
        snapshot = critic._exemplars
        assert snapshot is not None

        # Mutate the lists the caller handed in.
        bytes_list.clear()
        ids.clear()
        bytes_list.append(b"injected" * 20)
        ids.append("evil-id")

        # The critic still sees the original bound exemplars.
        assert critic._exemplars is snapshot
        assert len(snapshot) == 3
        assert snapshot[0].identity != "evil-id"


class TestParallelEvaluationDoesNotMisattribute:
    """End-to-end: concurrent evaluations always return identities that
    actually correspond to the byte content stored in the same record."""

    def test_concurrent_evaluate_pairs_id_with_actual_nearest(self) -> None:
        bytes_list, ids = _make_exemplars(8)
        critic = AestheticCritic(exemplars=bytes_list, exemplar_ids=ids)

        # Build a payload that is identical to one specific exemplar so
        # nearest_exemplar_id has a known correct value.
        target_idx = 4
        target_source = bytes_list[target_idx].decode("utf-8")
        expected_id = ids[target_idx]

        # id -> bytes lookup so we can verify the (id, content) pairing
        # even if the nearest happens to be a tie elsewhere.
        id_to_bytes = dict(zip(ids, bytes_list, strict=True))

        results: list[str | None] = []
        errors: list[BaseException] = []
        lock = threading.Lock()

        def worker() -> None:
            try:
                critique = critic.evaluate(target_source, "python")
                with lock:
                    results.append(critique.nearest_exemplar_id)
            except BaseException as exc:  # noqa: BLE001
                with lock:
                    errors.append(exc)

        with ThreadPoolExecutor(max_workers=16) as pool:
            futures = [pool.submit(worker) for _ in range(200)]
            for f in futures:
                f.result()

        assert errors == []
        assert len(results) == 200
        # Every reported id must still be a real exemplar, and on the
        # exact-match payload it must be the target id.
        for reported in results:
            assert reported is not None
            assert reported in id_to_bytes
            assert reported == expected_id

    def test_ncd_to_nearest_binding_pairs_correctly_in_parallel(self) -> None:
        """Tighter check on the binding-aware NCD primitive: the returned
        identity must be the identity of the actual nearest binding."""
        bytes_list, ids = _make_exemplars(12)
        bound = bind_exemplars(bytes_list, ids)
        assert bound is not None

        # Pick a few different probe payloads, each identical to a different
        # exemplar, and assert each thread sees the correct identity back.
        probes = [(bytes_list[i], ids[i]) for i in (0, 3, 7, 11)]

        errors: list[BaseException] = []

        def worker(probe: tuple[bytes, str]) -> None:
            payload, expected_id = probe
            try:
                for _ in range(50):
                    result = ncd_to_nearest_binding(payload, bound)
                    assert result is not None
                    _, identity = result
                    assert identity == expected_id
            except BaseException as exc:  # noqa: BLE001
                errors.append(exc)

        threads = [
            threading.Thread(target=worker, args=(probe,))
            for probe in probes * 8  # 32 threads, multiple probes
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == []


class TestSharedCriticAcrossThreads:
    """Smoke check: the concurrent serve scenario (one DynamicHelm shared
    across many request threads) is the deployed shape of this hazard.
    Exercise it by sharing a single AestheticCritic across many threads."""

    def test_shared_critic_many_evaluations_no_errors(self) -> None:
        bytes_list, ids = _make_exemplars(6)
        critic = AestheticCritic(exemplars=bytes_list, exemplar_ids=ids)

        sources = [
            "def add(a, b):\n    return a + b\n" * 4,
            "def mul(a, b):\n    return a * b\n" * 4,
            "class Foo:\n    def __init__(self, x):\n        self.x = x\n" * 3,
            "for i in range(100):\n    print(i)\n" * 5,
        ]

        errors: list[BaseException] = []

        def worker(source: str) -> None:
            try:
                for _ in range(25):
                    c = critic.evaluate(source, "python")
                    # Must always have a valid score, weights, and an id that,
                    # when present, is one of the configured ids.
                    assert 0.0 <= c.score.value <= 1.0
                    if c.nearest_exemplar_id is not None:
                        assert c.nearest_exemplar_id in ids
            except BaseException as exc:  # noqa: BLE001
                errors.append(exc)

        with ThreadPoolExecutor(max_workers=32) as pool:
            futures = [pool.submit(worker, src) for src in sources * 16]
            for f in futures:
                f.result()

        assert errors == []

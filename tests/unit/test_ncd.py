"""Unit tests for the NCD metric module (T008, T009)."""

from __future__ import annotations

import pytest
from eigenhelm.critic.ncd import ncd, ncd_to_exemplars

# Reusable test source strings
_QUICKSORT_SRC = (
    b"def quicksort(arr):\n    if len(arr) <= 1:\n"
    b"        return arr\n    pivot = arr[0]\n"
    b"    left = [x for x in arr[1:] if x <= pivot]\n"
    b"    right = [x for x in arr[1:] if x > pivot]\n"
    b"    return quicksort(left) + [pivot] + quicksort(right)\n"
)

_MERGESORT_SRC = (
    b"def mergesort(arr):\n    if len(arr) <= 1:\n"
    b"        return arr\n    mid = len(arr) // 2\n"
    b"    left = mergesort(arr[:mid])\n"
    b"    right = mergesort(arr[mid:])\n"
    b"    return merge(left, right)"
)

_TREENODE_SRC = (
    b"class TreeNode:\n    def __init__(self, val):\n"
    b"        self.val = val\n        self.left = None\n"
    b"        self.right = None\n"
)


class TestNcd:
    """Tests for the ncd() function."""

    def test_identical_strings_return_zero(self) -> None:
        x = _QUICKSORT_SRC * 3
        assert ncd(x, x) == pytest.approx(0.0, abs=0.05)

    def test_result_in_unit_interval(self) -> None:
        x = b"def quicksort(arr): return sorted(arr)"
        y = b"import random; random.shuffle(list(range(100)))"
        result = ncd(x, y)
        assert 0.0 <= result <= 1.0

    def test_symmetry(self) -> None:
        x = _QUICKSORT_SRC
        y = _TREENODE_SRC * 3
        assert ncd(x, y) == pytest.approx(ncd(y, x), abs=0.05)

    def test_determinism(self) -> None:
        x = b"def foo(): pass"
        y = b"def bar(): return 42"
        results = [ncd(x, y) for _ in range(10)]
        assert all(r == results[0] for r in results)

    def test_dissimilar_strings_higher_than_similar(self) -> None:
        base = _QUICKSORT_SRC
        similar = _MERGESORT_SRC
        different = b"x = 42\nprint(x)\n" * 10
        assert ncd(base, similar) < ncd(base, different)

    def test_empty_strings(self) -> None:
        result = ncd(b"", b"")
        assert 0.0 <= result <= 1.0


class TestNcdToExemplars:
    """Tests for the ncd_to_exemplars() function."""

    def test_returns_min_over_exemplar_set(self) -> None:
        source = _QUICKSORT_SRC
        exemplars = [
            source,  # identical — should give NCD ≈ 0
            b"import random; data = [random.randint(0, 1000) "
            b"for _ in range(100)]" * 3,
        ]
        result = ncd_to_exemplars(source, exemplars)
        assert result is not None
        assert result == pytest.approx(0.0, abs=0.05)

    def test_returns_none_for_short_input(self) -> None:
        source = b"x = 1"
        exemplars = [b"def foo(): pass" * 10]
        assert ncd_to_exemplars(source, exemplars) is None

    def test_returns_none_for_empty_exemplar_list(self) -> None:
        source = b"def foo(): pass" * 10
        assert ncd_to_exemplars(source, []) is None

    def test_min_bytes_threshold(self) -> None:
        source = b"a" * 49  # just under default threshold
        exemplars = [b"b" * 100]
        assert ncd_to_exemplars(source, exemplars) is None

        source = b"a" * 50  # at threshold
        result = ncd_to_exemplars(source, exemplars)
        assert result is not None

    def test_determinism(self) -> None:
        source = _QUICKSORT_SRC * 3
        exemplars = [_MERGESORT_SRC * 3]
        results = [ncd_to_exemplars(source, exemplars) for _ in range(10)]
        assert all(r == results[0] for r in results)

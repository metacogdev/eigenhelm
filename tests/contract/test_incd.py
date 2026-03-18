"""Contract tests for NCD metric — discrimination and backward compatibility (T011)."""

from __future__ import annotations

import numpy as np
import pytest
from eigenhelm.critic.ncd import ncd, ncd_to_exemplars

pytestmark = pytest.mark.contract


class TestNCDContract:
    """NCD contract invariants: discrimination and backward compat."""

    def test_ncd_discriminates_similar_vs_random(self) -> None:
        """In-corpus-like code scores low NCD; random bytes score high."""
        exemplar = (
            b"def quicksort(arr):\n"
            b"    if len(arr) <= 1:\n"
            b"        return arr\n"
            b"    pivot = arr[0]\n"
            b"    left = [x for x in arr[1:] if x <= pivot]\n"
            b"    right = [x for x in arr[1:] if x > pivot]\n"
            b"    return quicksort(left) + [pivot] + quicksort(right)\n"
        )
        similar = (
            b"def mergesort(arr):\n"
            b"    if len(arr) <= 1:\n"
            b"        return arr\n"
            b"    mid = len(arr) // 2\n"
            b"    left = mergesort(arr[:mid])\n"
            b"    right = mergesort(arr[mid:])\n"
            b"    return merge(left, right)\n"
        )
        rng = np.random.default_rng(42)
        random_bytes = bytes(rng.integers(0, 256, size=300, dtype=np.uint8))

        ncd_similar = ncd(exemplar, similar)
        ncd_random = ncd(exemplar, random_bytes)

        # Similar code should score lower than random bytes
        assert ncd_similar < ncd_random

    def test_ncd_to_exemplars_discrimination(self) -> None:
        """ncd_to_exemplars returns lower distance for corpus-like code."""
        exemplars = [
            (
                b"def quicksort(arr):\n    if len(arr) <= 1:\n"
                b"        return arr\n    pivot = arr[0]\n"
                b"    left = [x for x in arr[1:] if x <= pivot]\n"
                b"    right = [x for x in arr[1:] if x > pivot]\n"
                b"    return quicksort(left) + [pivot] + quicksort(right)\n"
            ),
            (
                b"def mergesort(arr):\n    if len(arr) <= 1:\n"
                b"        return arr\n    mid = len(arr) // 2\n"
                b"    left = mergesort(arr[:mid])\n"
                b"    right = mergesort(arr[mid:])\n"
                b"    return merge(left, right)\n"
            ),
        ]
        similar_source = (
            b"def bubblesort(arr):\n    n = len(arr)\n"
            b"    for i in range(n):\n"
            b"        for j in range(0, n-i-1):\n"
            b"            if arr[j] > arr[j+1]:\n"
            b"                arr[j], arr[j+1] = arr[j+1], arr[j]\n"
            b"    return arr\n"
        )
        rng = np.random.default_rng(99)
        random_source = bytes(rng.integers(0, 256, size=300, dtype=np.uint8))

        dist_similar = ncd_to_exemplars(similar_source, exemplars)
        dist_random = ncd_to_exemplars(random_source, exemplars)

        assert dist_similar is not None
        assert dist_random is not None
        assert dist_similar < dist_random

    def test_pre_010_model_loads_without_exemplars(self, synthetic_model) -> None:
        """Pre-010 models have exemplars=None and load without errors (FR-006)."""
        assert synthetic_model.exemplars is None
        assert synthetic_model.n_exemplars == 0

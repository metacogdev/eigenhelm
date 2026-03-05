"""Shannon entropy — byte-level H(P) over UTF-8 encoded source.

Reference: R-001 — byte-level entropy via collections.Counter.
"""

from __future__ import annotations

import math
from collections import Counter


def shannon_entropy(source: str) -> float:
    """Compute Shannon entropy H(P) in bits/byte over UTF-8 bytes.

    Args:
        source: Raw source code string.

    Returns:
        Entropy ∈ [0.0, 8.0]. Returns 0.0 for empty source.
    """
    if not source:
        return 0.0
    src_bytes = source.encode("utf-8")
    total = len(src_bytes)
    counts = Counter(src_bytes)
    entropy = 0.0
    for count in counts.values():
        p = count / total
        entropy -= p * math.log2(p)
    return entropy

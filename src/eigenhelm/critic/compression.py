"""zlib compression ratio — single-string Kolmogorov complexity approximation.

Reference: R-002 — zlib.compress(level=6), bypass for micro-snippets (SC-004).
"""

from __future__ import annotations

import zlib


def compression_ratio(source: str, min_bytes: int = 50) -> float | None:
    """Compute zlib compression ratio: compressed_size / raw_size.

    Returns None when source is empty or shorter than min_bytes, preventing
    zlib framing overhead from distorting the ratio on micro-snippets.

    Args:
        source:    Raw source code string.
        min_bytes: Minimum UTF-8 byte length to compute ratio (default: 50).

    Returns:
        Ratio ∈ (0, ∞), typically ≤ 1.2 for text. None when source is
        too short or empty.
    """
    if not source:
        return None
    src_bytes = source.encode("utf-8")
    if len(src_bytes) < min_bytes:
        return None
    compressed_size = len(zlib.compress(src_bytes, level=6))
    return compressed_size / len(src_bytes)

"""Normalized Compression Distance (NCD) metric.

Implements two-string NCD using zlib compression:
    NCD(x, y) = (C(xy) - min(C(x), C(y))) / max(C(x), C(y))

Reference: Cilibrasi & Vitanyi (2005), Li & Vitanyi (2008).
"""

from __future__ import annotations

import zlib


def ncd(x: bytes, y: bytes, *, level: int = 9) -> float:
    """Compute NCD between two byte strings. Returns value in [0.0, 1.0].

    Uses zlib at the specified compression level. Result is clamped to
    [0.0, 1.0] since zlib overhead can cause slight overshoot on small inputs.
    """
    cx = len(zlib.compress(x, level=level))
    cy = len(zlib.compress(y, level=level))
    cxy = len(zlib.compress(x + y, level=level))

    denominator = max(cx, cy)
    if denominator == 0:
        return 0.0

    result = (cxy - min(cx, cy)) / denominator
    return max(0.0, min(1.0, result))


def ncd_to_exemplars(
    source_bytes: bytes,
    exemplar_bytes: list[bytes],
    *,
    level: int = 9,
    min_bytes: int = 50,
) -> float | None:
    """Compute minimum NCD between source and all exemplars.

    Returns None if source is too short or exemplar list is empty.
    Returns min(NCD(source, e) for e in exemplars).
    """
    if len(source_bytes) < min_bytes or not exemplar_bytes:
        return None

    return min(ncd(source_bytes, e, level=level) for e in exemplar_bytes)


def ncd_to_exemplars_with_id(
    source_bytes: bytes,
    exemplar_bytes: list[bytes],
    exemplar_ids: list[str],
    *,
    level: int = 9,
    min_bytes: int = 50,
) -> tuple[float, str] | None:
    """Compute minimum NCD and return (distance, exemplar_id) of the nearest.

    Returns None if source is too short or exemplar list is empty.

    Raises:
        ValueError: If exemplar_bytes and exemplar_ids have different lengths.
    """
    if len(exemplar_bytes) != len(exemplar_ids):
        raise ValueError(
            f"exemplar_bytes ({len(exemplar_bytes)}) and "
            f"exemplar_ids ({len(exemplar_ids)}) must have the same length"
        )
    if len(source_bytes) < min_bytes or not exemplar_bytes:
        return None

    distances = [ncd(source_bytes, e, level=level) for e in exemplar_bytes]
    min_idx = min(range(len(distances)), key=lambda i: distances[i])
    return distances[min_idx], exemplar_ids[min_idx]

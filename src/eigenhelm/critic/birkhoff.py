"""Birkhoff Aesthetic Measure — information-theoretic order/complexity ratio.

Formula: M_Z = (N·H − K) / (N·H), clamped to [0.0, 1.0].
  N = raw_bytes, H = entropy (bits/byte), K = compressed_bytes.

Reference: R-003 — Birkhoff (1933); Rigau et al. (2008) IEEE CG&A.
"""

from __future__ import annotations


def birkhoff_measure(entropy: float, raw_bytes: int, compressed_bytes: int) -> float:
    """Compute Birkhoff Aesthetic Measure M_Z ∈ [0.0, 1.0].

    Args:
        entropy:          Shannon H(P) in bits/byte.
        raw_bytes:        len(source.encode("utf-8")).
        compressed_bytes: len(zlib.compress(source_bytes)).

    Returns:
        M_Z ∈ [0.0, 1.0]. Returns 0.0 when N·H == 0 (undefined structure)
        or when K > N·H (incompressible content, clamped).
    """
    nh = raw_bytes * entropy
    if nh == 0.0:
        return 0.0
    mz = (nh - compressed_bytes) / nh
    return max(0.0, min(1.0, mz))

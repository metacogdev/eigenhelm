"""Concurrency-safe exemplar identity bindings.

Exemplar attribution (the "nearest exemplar id" reported alongside an NCD
distance) requires bytes and identity to stay paired. Storing them in two
parallel lists permits the lists to drift across concurrent reads — an
in-flight evaluation can read fresh bytes and stale ids (or vice versa) and
return the wrong identity for the nearest exemplar.

This module binds (content, identity) into a single immutable record and
exposes a constructor that copies a pair of input sequences into a tuple of
those records. A single attribute read of the resulting tuple yields a
self-consistent snapshot, eliminating the drift hazard for any caller that
stores exemplars on shared mutable state (e.g., AestheticCritic).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class ExemplarBinding:
    """Immutable pair: exemplar bytes + the identity reported on attribution.

    ``identity`` is an empty string when no identity was supplied at
    construction; callers reporting attribution should treat the empty string
    as "unknown" rather than as a real exemplar id.
    """

    content: bytes
    identity: str


def bind_exemplars(
    exemplar_bytes: Sequence[bytes] | None,
    exemplar_ids: Sequence[str] | None,
) -> tuple[ExemplarBinding, ...] | None:
    """Bind two parallel sequences into one immutable tuple of pairs.

    Returns ``None`` when ``exemplar_bytes`` is ``None`` (no exemplar
    attribution configured). Returns an empty tuple when ``exemplar_bytes``
    is an empty sequence.

    Raises:
        ValueError: When ``exemplar_ids`` is provided with a different length
            than ``exemplar_bytes``. Failing at bind time keeps the in-flight
            evaluation path free of length checks and surfaces misconfiguration
            at construction rather than first call.
    """
    if exemplar_bytes is None:
        return None
    if exemplar_ids is None:
        return tuple(ExemplarBinding(content=b, identity="") for b in exemplar_bytes)
    if len(exemplar_bytes) != len(exemplar_ids):
        raise ValueError(
            f"exemplar_bytes ({len(exemplar_bytes)}) and "
            f"exemplar_ids ({len(exemplar_ids)}) must have the same length"
        )
    return tuple(
        ExemplarBinding(content=b, identity=i)
        for b, i in zip(exemplar_bytes, exemplar_ids, strict=True)
    )

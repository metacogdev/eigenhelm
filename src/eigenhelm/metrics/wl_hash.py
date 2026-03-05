"""Weisfeiler-Leman graph hash histogram for AST nodes.

Reference: Shervashidze, N., Schweitzer, P., van Leeuwen, E.J., Mehlhorn, K.,
           and Borgwardt, K.M. (2011). Weisfeiler-Lehman graph kernels.
           Journal of Machine Learning Research, 12:2539-2561.

Algorithm (adapted for trees):
  1. Initialize: label each node with blake2b(node.type).
  2. Refine h iterations (default 3, max 5, capped at tree depth):
       label[v] = blake2b(label[v] || sorted(child labels))
  3. Histogram: map all labels (across all iterations) into 64 bins via
       bin = label_hash % 64
     Then normalize to probability distribution (sum = 1).

Hash function: hashlib.blake2b with 8-byte digest.
  - Deterministic across Python sessions (unlike hash()).
  - Faster than MD5 on modern CPUs.
  - 64-bit output fits into uint64; modulo 64 for bin mapping.
"""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    import tree_sitter

WL_BINS = 64
_DIGEST_SIZE = 8  # bytes → 64-bit hash


def _node_hash(value: str) -> int:
    """Hash a string to a uint64 using blake2b."""
    return int(
        hashlib.blake2b(value.encode("utf-8"), digest_size=_DIGEST_SIZE).hexdigest(),
        16,
    )


def _tree_depth(node: tree_sitter.Node) -> int:
    """Compute maximum depth of an AST subtree."""
    if not node.children:
        return 0
    return 1 + max(_tree_depth(c) for c in node.children)


def compute(ast_root: tree_sitter.Node, iterations: int = 3) -> np.ndarray:
    """Compute a 64-bin WL hash histogram from an AST.

    Args:
        ast_root: Root node of the Tree-sitter AST.
        iterations: WL refinement depth (1–5). Capped at actual tree depth.

    Returns:
        numpy.ndarray of shape (64,), dtype float64.
        Values sum to 1.0 (probability distribution).
        Returns a zero vector if the AST has no nodes.
    """
    iterations = max(1, min(iterations, 5))

    # Collect all nodes via iterative DFS (avoids recursion limit on deep trees).
    all_nodes: list[tree_sitter.Node] = []
    stack = [ast_root]
    while stack:
        node = stack.pop()
        all_nodes.append(node)
        stack.extend(reversed(node.children))

    if not all_nodes:
        return np.zeros(WL_BINS, dtype=np.float64)

    depth = _tree_depth(ast_root)
    actual_iters = min(iterations, max(depth, 1))

    # Node id → list of labels (one per iteration including init).
    labels: dict[int, list[int]] = {id(n): [_node_hash(n.type)] for n in all_nodes}

    for _ in range(actual_iters):
        new_labels: dict[int, int] = {}
        for node in all_nodes:
            nid = id(node)
            child_labels = sorted(str(labels[id(c)][-1]) for c in node.children if id(c) in labels)
            aggregated = str(labels[nid][-1]) + "||" + "||".join(child_labels)
            new_labels[nid] = _node_hash(aggregated)

        for nid, lbl in new_labels.items():
            labels[nid].append(lbl)

    # Build histogram across all nodes and all iterations.
    histogram = np.zeros(WL_BINS, dtype=np.uint64)
    for label_list in labels.values():
        for lbl in label_list:
            histogram[lbl % WL_BINS] += 1

    total = histogram.sum()
    if total == 0:
        return np.zeros(WL_BINS, dtype=np.float64)

    return histogram.astype(np.float64) / float(total)

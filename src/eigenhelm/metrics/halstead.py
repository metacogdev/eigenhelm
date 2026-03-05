"""Halstead complexity metrics from AST-structural node classification.

Reference: Halstead, M.H. (1977). Elements of Software Science.
           Elsevier North-Holland.

Classification strategy (language-agnostic, per clarification session):
  Operators — branch, control-flow, call, assignment, return nodes
  Operands  — leaf identifier and literal nodes (node.child_count == 0
              and node.type in identifier/literal categories)

Formulas:
  η  = η₁ + η₂           (vocabulary)
  N  = N₁ + N₂           (length)
  V  = N * log2(η)        (volume)
  D  = (η₁/2) * (N₂/η₂)  (difficulty)
  E  = D * V              (effort)
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from eigenhelm.models import HalsteadMetrics
from eigenhelm.parsers.language_map import OPERATOR_NODE_TYPES

if TYPE_CHECKING:
    import tree_sitter

# Leaf node type suffixes that identify operands.
_OPERAND_TYPE_SUBSTRINGS: tuple[str, ...] = (
    "identifier",
    "name",
    "literal",
    "number",
    "string",
    "integer",
    "float",
    "boolean",
    "true",
    "false",
    "null",
    "nil",
    "none",
)


def _is_operand_leaf(node: tree_sitter.Node) -> bool:
    """True if this is a leaf node representing an operand."""
    if node.child_count != 0:
        return False
    t = node.type.lower()
    return any(sub in t for sub in _OPERAND_TYPE_SUBSTRINGS)


def _is_operator(node: tree_sitter.Node) -> bool:
    """True if this node represents an operator (structural control node)."""
    return node.type in OPERATOR_NODE_TYPES


def compute(ast_root: tree_sitter.Node) -> HalsteadMetrics:
    """Compute Halstead metrics from a Tree-sitter AST root node.

    Args:
        ast_root: Root node from tree_sitter parser.

    Returns:
        HalsteadMetrics with V, D, E and raw counts.
    """
    operators: list[str] = []
    operands: list[str] = []

    def walk(node: tree_sitter.Node) -> None:
        if _is_operator(node):
            operators.append(node.type)
        elif _is_operand_leaf(node):
            text = node.text.decode("utf-8") if node.text else node.type
            operands.append(text)
        for child in node.children:
            walk(child)

    walk(ast_root)

    n1 = len(operators)
    n2 = len(operands)
    eta1 = len(set(operators))
    eta2 = len(set(operands))

    eta = eta1 + eta2
    n = n1 + n2

    if eta < 2 or n == 0:
        # Degenerate case: not enough vocabulary for meaningful metrics.
        return HalsteadMetrics(
            volume=0.0,
            difficulty=0.0,
            effort=0.0,
            distinct_operators=eta1,
            distinct_operands=eta2,
            total_operators=n1,
            total_operands=n2,
        )

    volume = n * math.log2(eta)
    difficulty = (eta1 / 2.0) * (n2 / eta2) if eta2 > 0 else 0.0
    effort = difficulty * volume

    return HalsteadMetrics(
        volume=volume,
        difficulty=difficulty,
        effort=effort,
        distinct_operators=eta1,
        distinct_operands=eta2,
        total_operators=n1,
        total_operands=n2,
    )

"""Data models for declaration-aware scoring."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DeclarationType(Enum):
    """Classification of detected declaration constructs."""

    TYPE_DEFINITION = "type_definition"
    ENUM_DECLARATION = "enum_declaration"
    CONST_TABLE = "const_table"
    CONFIG_MODEL = "config_model"
    FIELD_ONLY_CLASS = "field_only_class"


@dataclass(frozen=True)
class DeclarationRegion:
    """A detected declaration construct within a source file.

    The start_line/end_line span the enclosing construct, while
    declaration_line_count counts only the lines within that span
    that are purely declarative (field annotations, enum variants, etc.)
    — excluding method bodies.
    """

    declaration_type: DeclarationType
    start_line: int  # 1-indexed
    end_line: int  # 1-indexed, inclusive
    declaration_line_count: int
    language: str
    node_name: str

    def __post_init__(self) -> None:
        if self.start_line > self.end_line:
            raise ValueError(
                f"start_line ({self.start_line}) must be <= end_line ({self.end_line})"
            )
        if self.declaration_line_count < 1:
            raise ValueError(
                f"declaration_line_count must be >= 1, got {self.declaration_line_count}"
            )
        span = self.end_line - self.start_line + 1
        if self.declaration_line_count > span:
            raise ValueError(
                f"declaration_line_count ({self.declaration_line_count}) "
                f"exceeds span ({span})"
            )


@dataclass(frozen=True)
class DeclarationAnalysis:
    """Aggregated declaration analysis for a single file."""

    regions: tuple[DeclarationRegion, ...]
    declaration_lines: int
    non_blank_non_comment_lines: int
    ratio: float  # [0.0, 1.0]

    @property
    def is_dominant(self) -> bool:
        """True when ≥60% of non-blank, non-comment lines are declarations."""
        return self.ratio >= 0.6

    @property
    def is_pure_types(self) -> bool:
        """True when dominant AND all regions are type definitions or enums.

        Pure type files (dataclasses, Protocols, interfaces, structs) have
        no actionable signal from WL hash — the repetition is inherent to
        the syntax, not a design smell. These files should be skipped.
        """
        if not self.is_dominant or not self.regions:
            return False
        _TYPE_KINDS = frozenset(
            {
                DeclarationType.TYPE_DEFINITION,
                DeclarationType.ENUM_DECLARATION,
                DeclarationType.FIELD_ONLY_CLASS,
                DeclarationType.CONFIG_MODEL,
            }
        )
        return all(r.declaration_type in _TYPE_KINDS for r in self.regions)

    def __post_init__(self) -> None:
        if not (0.0 <= self.ratio <= 1.0):
            raise ValueError(f"ratio must be in [0.0, 1.0], got {self.ratio}")
        if self.declaration_lines > self.non_blank_non_comment_lines:
            raise ValueError(
                f"declaration_lines ({self.declaration_lines}) exceeds "
                f"non_blank_non_comment_lines ({self.non_blank_non_comment_lines})"
            )

"""Extended tests for declaration models — covers validation branches."""

from __future__ import annotations

import pytest
from eigenhelm.declarations.models import (
    DeclarationAnalysis,
    DeclarationRegion,
    DeclarationType,
)


class TestDeclarationRegionValidation:
    """Cover __post_init__ validation in DeclarationRegion."""

    def test_start_line_greater_than_end_line_raises(self) -> None:
        with pytest.raises(ValueError, match="start_line"):
            DeclarationRegion(
                declaration_type=DeclarationType.TYPE_DEFINITION,
                start_line=10,
                end_line=5,
                declaration_line_count=1,
                language="python",
                node_name="Foo",
            )

    def test_declaration_line_count_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="declaration_line_count must be >= 1"):
            DeclarationRegion(
                declaration_type=DeclarationType.TYPE_DEFINITION,
                start_line=1,
                end_line=5,
                declaration_line_count=0,
                language="python",
                node_name="Foo",
            )

    def test_declaration_line_count_exceeds_span_raises(self) -> None:
        with pytest.raises(ValueError, match="exceeds span"):
            DeclarationRegion(
                declaration_type=DeclarationType.TYPE_DEFINITION,
                start_line=1,
                end_line=3,
                declaration_line_count=5,
                language="python",
                node_name="Foo",
            )


class TestDeclarationAnalysisValidation:
    """Cover __post_init__ validation in DeclarationAnalysis."""

    def test_ratio_out_of_range_raises(self) -> None:
        with pytest.raises(ValueError, match="ratio must be in"):
            DeclarationAnalysis(
                regions=(),
                declaration_lines=0,
                non_blank_non_comment_lines=10,
                ratio=1.5,
            )

    def test_declaration_lines_exceeds_nbnc_raises(self) -> None:
        with pytest.raises(ValueError, match="exceeds"):
            DeclarationAnalysis(
                regions=(),
                declaration_lines=20,
                non_blank_non_comment_lines=10,
                ratio=0.5,
            )

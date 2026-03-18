"""Source location extraction for attribution.

Maps attributions back to source code locations using existing CodeUnit
metadata or full-source ranges.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from eigenhelm.attribution.models import SourceLocation

if TYPE_CHECKING:
    from eigenhelm.models import CodeUnit


def source_location_from_code_unit(code_unit: CodeUnit) -> SourceLocation:
    """Extract SourceLocation from a CodeUnit's metadata."""
    return SourceLocation(
        code_unit_name=code_unit.name,
        start_line=code_unit.start_line,
        end_line=code_unit.end_line,
        file_path=code_unit.file_path,
    )


def source_location_from_source(
    source: str, file_path: str | None = None
) -> SourceLocation:
    """Create a SourceLocation covering the full evaluated source."""
    if source:
        # Count lines: strip trailing newline to avoid overcounting
        lines = source.rstrip("\n").split("\n")
        end_line = len(lines)
    else:
        end_line = 1

    return SourceLocation(
        code_unit_name="<source>",
        start_line=1,
        end_line=end_line,
        file_path=file_path,
    )

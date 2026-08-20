"""Declaration-aware scoring: detection and analysis.

Detects declaration-dominant regions in source files using language-specific
tree-sitter AST analysis. Used to adjust directive categories and dampen
scores for files that are primarily type definitions or data tables.

Public API:
    detect_declarations() — find declaration constructs in source
    analyze_declarations() — compute declaration ratio and dominance
"""

from __future__ import annotations

from eigenhelm.declarations.models import (
    DeclarationAnalysis,
    DeclarationRegion,
    DeclarationType,
)

__all__ = [
    "DeclarationAnalysis",
    "DeclarationRegion",
    "DeclarationType",
    "analyze_declarations",
    "detect_declarations",
]


def detect_declarations(source: str, language: str) -> tuple[DeclarationRegion, ...]:
    """Detect declaration constructs in source code.

    Uses language-specific tree-sitter AST analysis. Returns an empty
    tuple for unsupported languages, empty source, or unparseable source
    (conservative — no false positives).

    Args:
        source: Source code string (may be empty).
        language: Language identifier (may be unsupported).

    Returns:
        Tuple of DeclarationRegion sorted by start_line, non-overlapping.
    """
    if not source.strip():
        return ()

    if language == "python":
        from eigenhelm.declarations.python import detect

        return detect(source)
    if language == "rust":
        from eigenhelm.declarations.rust import detect

        return detect(source)
    if language == "typescript":
        from eigenhelm.declarations.typescript import detect

        return detect(source)
    if language == "javascript":
        from eigenhelm.declarations.javascript import detect

        return detect(source)
    if language == "go":
        from eigenhelm.declarations.go import detect

        return detect(source)

    return ()


def analyze_declarations(source: str, language: str) -> DeclarationAnalysis:
    """Compute aggregated declaration analysis for a file.

    ``declaration_lines`` is the number of non-blank, non-comment lines that
    fall inside a detected declaration region — the numerator and denominator
    of ``ratio`` count the same population of lines, so the ratio is a true
    fraction in [0, 1]. Summing per-region ``declaration_line_count`` instead
    breaks that invariant (and aborted whole runs on real files): detectors
    count non-blank lines, so a struct documented with a comment per field
    puts lines in the numerator that the denominator excludes.

    Args:
        source: Source code string (may be empty).
        language: Language identifier (may be unsupported).

    Returns:
        DeclarationAnalysis with regions, line counts, ratio, and is_dominant.
    """
    regions = detect_declarations(source, language)
    nbnc_lines = _non_blank_non_comment_line_numbers(source, language)

    covered: set[int] = set()
    for r in regions:
        covered.update(range(r.start_line, r.end_line + 1))
    decl_lines = len(nbnc_lines & covered)

    nbnc = len(nbnc_lines)
    ratio = decl_lines / nbnc if nbnc > 0 else 0.0

    return DeclarationAnalysis(
        regions=regions,
        declaration_lines=decl_lines,
        non_blank_non_comment_lines=nbnc,
        ratio=ratio,
    )


def _non_blank_non_comment_line_numbers(source: str, language: str) -> set[int]:
    """1-indexed line numbers of non-blank, non-comment lines in source."""
    if not source.strip():
        return set()

    comment_prefixes = _COMMENT_PREFIXES.get(language, ("#",))
    numbers: set[int] = set()
    in_block_comment = False
    block_start, block_end = _BLOCK_COMMENT.get(language, (None, None))

    for lineno, line in enumerate(source.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue

        # Handle block comments
        if block_start and block_end:
            if in_block_comment:
                if block_end in stripped:
                    in_block_comment = False
                continue
            if stripped.startswith(block_start):
                if block_end not in stripped[len(block_start) :]:
                    in_block_comment = True
                continue

        # Handle line comments
        if any(stripped.startswith(p) for p in comment_prefixes):
            continue

        numbers.add(lineno)

    return numbers


_COMMENT_PREFIXES: dict[str, tuple[str, ...]] = {
    "python": ("#",),
    "javascript": ("//",),
    "typescript": ("//",),
    "go": ("//",),
    "rust": ("//",),
}

_BLOCK_COMMENT: dict[str, tuple[str, str]] = {
    "javascript": ("/*", "*/"),
    "typescript": ("/*", "*/"),
    "go": ("/*", "*/"),
    "rust": ("/*", "*/"),
}

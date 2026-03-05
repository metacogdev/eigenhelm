"""Tree-sitter AST parsing and code unit extraction.

Parses source code and yields CodeUnit objects (one per function/method/class).
Uses tree-sitter-language-pack for grammar bundles — adding a new language requires
only a LANGUAGE_MAP entry, no code changes here.
Falls back to tree-sitter-languages if language-pack is unavailable, and gracefully degrades to
a single unit if tree-sitter is not installed at all.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING

from eigenhelm.models import CodeUnit, UnsupportedLanguageError
from eigenhelm.parsers.language_map import get_grammar_name, is_supported

if TYPE_CHECKING:
    import tree_sitter

try:
    from tree_sitter_language_pack import get_parser as _get_parser

    _HAS_TREE_SITTER = True
except ImportError:
    try:
        from tree_sitter_languages import get_parser as _get_parser

        _HAS_TREE_SITTER = True
    except ImportError:
        _HAS_TREE_SITTER = False


# AST node types that represent extractable top-level code units.
_UNIT_NODE_TYPES: frozenset[str] = frozenset(
    {
        "function_definition",  # Python
        "function_declaration",  # JavaScript / Go / Java / Rust
        "method_definition",  # JavaScript class methods
        "method_declaration",  # Java
        "impl_item",  # Rust impl blocks
        "function_item",  # Rust fn
        "class_definition",  # Python
        "class_declaration",  # Java / JS
        "func_declaration",  # Go
        "func_literal",  # Go closures
    }
)


def parse_source(source: str, language: str) -> tree_sitter.Node | None:
    """Parse source code and return the AST root node.

    Args:
        source: Raw source code string.
        language: Language identifier (e.g., "python").

    Returns:
        Root AST node, or None if tree-sitter is unavailable.

    Raises:
        UnsupportedLanguageError: If no grammar registered for language.
    """
    if not is_supported(language):
        raise UnsupportedLanguageError(language)

    if not _HAS_TREE_SITTER:
        return None

    grammar_name = get_grammar_name(language)
    parser = _get_parser(grammar_name)
    tree = parser.parse(source.encode("utf-8"))
    return tree.root_node


def extract_units(source: str, language: str, file_path: str | None = None) -> list[CodeUnit]:
    """Split source code into extractable CodeUnit objects.

    Attempts Tree-sitter parsing to find function/class boundaries.
    Falls back to treating the entire source as a single unit if parsing
    is unavailable or no sub-units are found.

    Args:
        source: Raw source code string.
        language: Language identifier.
        file_path: Optional source file path for annotations.

    Returns:
        List of CodeUnit objects, one per function/method/class found.
        If no sub-units detected, returns a single unit wrapping all source.

    Raises:
        UnsupportedLanguageError: If language has no registered grammar.
    """
    if not source.strip():
        return []

    if not is_supported(language):
        raise UnsupportedLanguageError(language)

    root = parse_source(source, language)
    if root is None:
        return _fallback_unit(source, language, file_path)

    units = list(_collect_units(root, source, language, file_path))

    # If no named units found, treat entire source as one anonymous unit.
    if not units:
        return _fallback_unit(source, language, file_path)

    return units


def extract_units_partial(
    source: str,
    language: str,
    file_path: str | None = None,
) -> tuple[list[CodeUnit], bool]:
    """Like extract_units but catches syntax errors, returning partial results.

    Returns:
        Tuple of (units, partial_parse_flag).
        partial_parse_flag is True if the AST contained ERROR nodes.
    """
    if not is_supported(language):
        return [], False  # caller converts to UnsupportedLanguageError

    root = parse_source(source, language)
    if root is None:
        units = _fallback_unit(source, language, file_path)
        return units, False

    has_errors = _has_error_nodes(root)
    units = list(_collect_units(root, source, language, file_path))
    if not units:
        units = _fallback_unit(source, language, file_path)

    return units, has_errors


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _collect_units(
    root: tree_sitter.Node,
    source: str,
    language: str,
    file_path: str | None,
) -> Iterator[CodeUnit]:
    """Walk the AST and yield top-level function/class nodes as CodeUnits."""
    source_lines = source.splitlines()

    def walk(node: tree_sitter.Node, depth: int = 0) -> Iterator[CodeUnit]:
        if node.type in _UNIT_NODE_TYPES:
            name = _extract_name(node)
            start_line = node.start_point[0] + 1  # 1-based
            end_line = node.end_point[0] + 1

            unit_lines = source_lines[start_line - 1 : end_line]
            unit_source = "\n".join(unit_lines)

            yield CodeUnit(
                source=unit_source,
                language=language,
                name=name,
                start_line=start_line,
                end_line=end_line,
                file_path=file_path,
            )
            # Do not recurse into nested functions/methods to avoid duplicates
            # at this depth.
            return

        for child in node.children:
            yield from walk(child, depth + 1)

    yield from walk(root)


def _extract_name(node: tree_sitter.Node) -> str:
    """Extract the identifier name from a function/class node."""
    for child in node.children:
        if child.type == "identifier":
            return child.text.decode("utf-8") if child.text else "<anonymous>"
    return "<anonymous>"


def _fallback_unit(source: str, language: str, file_path: str | None) -> list[CodeUnit]:
    """Return a single CodeUnit wrapping the entire source."""
    lines = source.splitlines()
    return [
        CodeUnit(
            source=source,
            language=language,
            name="<module>",
            start_line=1,
            end_line=len(lines),
            file_path=file_path,
        )
    ]


def _has_error_nodes(node: tree_sitter.Node) -> bool:
    """Return True if any ERROR node exists in the AST (syntax errors)."""
    if node.type == "ERROR" or node.is_missing:
        return True
    return any(_has_error_nodes(child) for child in node.children)

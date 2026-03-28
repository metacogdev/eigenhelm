"""TypeScript declaration detection via tree-sitter.

Detects interface, type alias, enum, and const-table declarations.
"""

from __future__ import annotations

from eigenhelm.declarations.models import DeclarationRegion, DeclarationType


def detect(source: str) -> tuple[DeclarationRegion, ...]:
    """Detect TypeScript declaration constructs.

    Finds:
    - Interface declarations (``interface Foo { ... }``)
    - Type alias declarations (``type Foo = ...``)
    - Enum declarations (``enum Foo { A, B, C }``)
    - Module-level const arrays of object literals

    Does NOT detect classes with method implementations or functions.

    Returns:
        Sorted DeclarationRegion entries.
    """
    from eigenhelm.parsers.tree_sitter import parse_source

    root = parse_source(source, "typescript")
    if root is None:
        return ()

    regions: list[DeclarationRegion] = []

    for node in root.children:
        _visit_top_level(node, source, regions)

    regions.sort(key=lambda r: r.start_line)
    return tuple(regions)


def _visit_top_level(
    node,
    source: str,
    regions: list[DeclarationRegion],
) -> None:
    """Dispatch a top-level AST node to the appropriate detector."""
    # Unwrap export statements to inspect the inner declaration.
    if node.type == "export_statement":
        for child in node.children:
            _visit_top_level(child, source, regions)
        return

    if node.type == "interface_declaration":
        _handle_interface(node, source, regions)
    elif node.type == "type_alias_declaration":
        _handle_type_alias(node, source, regions)
    elif node.type == "enum_declaration":
        _handle_enum(node, source, regions)
    elif node.type == "lexical_declaration":
        _handle_const_table(node, source, regions)


# ---------------------------------------------------------------------------
# Interface declarations
# ---------------------------------------------------------------------------


def _handle_interface(node, source: str, regions: list[DeclarationRegion]) -> None:
    """Detect ``interface Foo { ... }``."""
    name = _extract_name(node)
    start, end = _line_span(node)
    line_count = _non_blank_line_count(source, start, end)

    regions.append(
        DeclarationRegion(
            declaration_type=DeclarationType.TYPE_DEFINITION,
            start_line=start,
            end_line=end,
            declaration_line_count=line_count,
            language="typescript",
            node_name=name,
        )
    )


# ---------------------------------------------------------------------------
# Type alias declarations
# ---------------------------------------------------------------------------


def _handle_type_alias(node, source: str, regions: list[DeclarationRegion]) -> None:
    """Detect ``type Foo = ...``."""
    name = _extract_name(node)
    start, end = _line_span(node)
    line_count = _non_blank_line_count(source, start, end)

    regions.append(
        DeclarationRegion(
            declaration_type=DeclarationType.TYPE_DEFINITION,
            start_line=start,
            end_line=end,
            declaration_line_count=line_count,
            language="typescript",
            node_name=name,
        )
    )


# ---------------------------------------------------------------------------
# Enum declarations
# ---------------------------------------------------------------------------


def _handle_enum(node, source: str, regions: list[DeclarationRegion]) -> None:
    """Detect ``enum Foo { A, B, C }`` (value-only, no computed members)."""
    if _has_computed_enum_members(node):
        return

    name = _extract_name(node)
    start, end = _line_span(node)
    line_count = _non_blank_line_count(source, start, end)

    regions.append(
        DeclarationRegion(
            declaration_type=DeclarationType.ENUM_DECLARATION,
            start_line=start,
            end_line=end,
            declaration_line_count=line_count,
            language="typescript",
            node_name=name,
        )
    )


def _has_computed_enum_members(node) -> bool:
    """Return True if any enum member has a computed (non-literal) initializer."""
    body = _find_child_by_type(node, "enum_body")
    if body is None:
        return False

    for member in body.children:
        if member.type != "enum_member":
            continue
        # Check if member has an initializer that is not a simple literal.
        for child in member.children:
            if child.type == "=":
                # The value follows the '=' — check the next sibling.
                value = child.next_sibling
                if value is not None and not _is_literal(value):
                    return True
    return False


def _is_literal(node) -> bool:
    """Return True for simple literal values (string, number, true, false)."""
    literal_types = {
        "string",
        "number",
        "true",
        "false",
        "template_string",
    }
    return node.type in literal_types


# ---------------------------------------------------------------------------
# Const tables: const FOO = [{...}, {...}]
# ---------------------------------------------------------------------------


def _handle_const_table(node, source: str, regions: list[DeclarationRegion]) -> None:
    """Detect module-level ``const FOO = [{...}, {...}]``."""
    if not _is_const_declaration(node):
        return

    for child in node.children:
        if child.type != "variable_declarator":
            continue

        name = _extract_name(child)
        value = _find_child_by_type(child, "array")
        if value is None:
            continue

        if not _is_array_of_object_literals(value):
            continue

        start, end = _line_span(node)
        line_count = _non_blank_line_count(source, start, end)

        regions.append(
            DeclarationRegion(
                declaration_type=DeclarationType.CONST_TABLE,
                start_line=start,
                end_line=end,
                declaration_line_count=line_count,
                language="typescript",
                node_name=name,
            )
        )


def _is_const_declaration(node) -> bool:
    """Return True if lexical_declaration uses ``const``."""
    for child in node.children:
        if child.type == "const":
            return True
    return False


def _is_array_of_object_literals(node) -> bool:
    """Return True if the array contains only object literals (ignoring commas)."""
    has_object = False
    for child in node.children:
        if child.type in ("[", "]", ",", "comment"):
            continue
        if child.type == "object":
            has_object = True
        else:
            return False
    return has_object


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _extract_name(node) -> str:
    """Extract the identifier name from an AST node."""
    for child in node.children:
        if child.type in ("identifier", "type_identifier"):
            text = child.text
            if text is None:
                return ""
            return text.decode("utf-8") if isinstance(text, bytes) else text
    return ""


def _find_child_by_type(node, type_name: str):
    """Return the first child matching *type_name*, or None."""
    for child in node.children:
        if child.type == type_name:
            return child
    return None


def _line_span(node) -> tuple[int, int]:
    """Return 1-indexed (start_line, end_line) for a node."""
    return node.start_point[0] + 1, node.end_point[0] + 1


def _non_blank_line_count(source: str, start: int, end: int) -> int:
    """Count non-blank lines within the 1-indexed [start, end] span."""
    lines = source.splitlines()[start - 1 : end]
    return sum(1 for line in lines if line.strip())

"""JavaScript declaration detection via tree-sitter.

Detects const tables (arrays of object literals) and field-only classes.
"""

from __future__ import annotations

from eigenhelm.declarations.models import DeclarationRegion, DeclarationType


def detect(source: str) -> tuple[DeclarationRegion, ...]:
    """Detect JavaScript declaration constructs.

    Finds:
    - Module-level ``const FOO = [{...}, {...}]`` (CONST_TABLE)
    - Classes with only field declarations, no method bodies (FIELD_ONLY_CLASS)

    Handles ``export_statement`` wrapping around declarations.

    Returns:
        Sorted DeclarationRegion entries (by start_line).
    """
    from eigenhelm.parsers.tree_sitter import parse_source

    root = parse_source(source, "javascript")
    if root is None:
        return ()

    lines = source.splitlines()
    regions: list[DeclarationRegion] = []

    for node in root.children:
        _visit_top_level(node, lines, regions)

    regions.sort(key=lambda r: r.start_line)
    return tuple(regions)


def _visit_top_level(node, lines: list[str], regions: list[DeclarationRegion]) -> None:
    """Process a top-level AST node, unwrapping export_statement."""
    if node.type == "export_statement":
        for child in node.children:
            if child.type in ("lexical_declaration", "class_declaration"):
                _check_node(child, lines, regions)
    elif node.type in ("lexical_declaration", "class_declaration"):
        _check_node(node, lines, regions)


def _check_node(node, lines: list[str], regions: list[DeclarationRegion]) -> None:
    """Dispatch detection for a declaration or class node."""
    if node.type == "lexical_declaration":
        _check_const_table(node, lines, regions)
    elif node.type == "class_declaration":
        _check_field_only_class(node, lines, regions)


def _check_const_table(
    node, lines: list[str], regions: list[DeclarationRegion]
) -> None:
    """Detect ``const NAME = [{...}, ...]`` patterns."""
    # Must use const keyword
    if not _has_const_keyword(node):
        return

    # Find the variable declarator
    for child in node.children:
        if child.type == "variable_declarator":
            name = _extract_declarator_name(child)
            value = _extract_declarator_value(child)
            if (
                value is not None
                and value.type == "array"
                and _is_array_of_objects(value)
            ):
                start = node.start_point[0] + 1
                end = node.end_point[0] + 1
                regions.append(
                    DeclarationRegion(
                        declaration_type=DeclarationType.CONST_TABLE,
                        start_line=start,
                        end_line=end,
                        declaration_line_count=_count_non_blank(lines, start, end),
                        language="javascript",
                        node_name=name,
                    )
                )


def _check_field_only_class(
    node, lines: list[str], regions: list[DeclarationRegion]
) -> None:
    """Detect classes with only field declarations (no method bodies)."""
    name = _extract_name(node)
    body = _find_child_by_type(node, "class_body")
    if body is None:
        return

    has_fields = False
    for member in body.children:
        # Skip braces
        if member.type in ("{", "}"):
            continue
        # Skip decorators, semicolons, comments
        if member.type in ("decorator", ";", "comment"):
            continue
        if member.type == "method_definition":
            # Methods with bodies disqualify the class
            return
        if member.type in (
            "field_definition",
            "public_field_definition",
            "property_definition",
        ):
            has_fields = True
        else:
            # Unknown member type — conservative, skip this class
            return

    if not has_fields:
        return

    start = node.start_point[0] + 1
    end = node.end_point[0] + 1
    regions.append(
        DeclarationRegion(
            declaration_type=DeclarationType.FIELD_ONLY_CLASS,
            start_line=start,
            end_line=end,
            declaration_line_count=_count_non_blank(lines, start, end),
            language="javascript",
            node_name=name,
        )
    )


# --- Helpers ---


def _has_const_keyword(node) -> bool:
    """Check if a lexical_declaration uses ``const``."""
    for child in node.children:
        if child.type == "const":
            return True
    return False


def _extract_declarator_name(node) -> str:
    """Extract the name from a variable_declarator."""
    for child in node.children:
        if child.type == "identifier":
            text = child.text
            if text is None:
                return ""
            return text.decode("utf-8") if isinstance(text, bytes) else text
    return ""


def _extract_declarator_value(node):
    """Extract the value node from a variable_declarator (RHS of ``=``)."""
    saw_eq = False
    for child in node.children:
        if saw_eq:
            return child
        if child.type == "=":
            saw_eq = True
    return None


def _is_array_of_objects(array_node) -> bool:
    """Check if an array node contains only object expressions."""
    has_objects = False
    for child in array_node.children:
        if child.type in ("[", "]", ","):
            continue
        if child.type == "comment":
            continue
        if child.type == "object":
            has_objects = True
        else:
            return False
    return has_objects


def _extract_name(node) -> str:
    """Extract the identifier name from a class node."""
    for child in node.children:
        if child.type == "identifier":
            text = child.text
            if text is None:
                return ""
            return text.decode("utf-8") if isinstance(text, bytes) else text
    return ""


def _find_child_by_type(node, type_name: str):
    """Find the first child with the given type."""
    for child in node.children:
        if child.type == type_name:
            return child
    return None


def _count_non_blank(lines: list[str], start: int, end: int) -> int:
    """Count non-blank lines in a 1-indexed inclusive range."""
    count = 0
    for i in range(start - 1, min(end, len(lines))):
        if lines[i].strip():
            count += 1
    return max(count, 1)

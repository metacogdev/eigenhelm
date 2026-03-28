"""Rust declaration detection via tree-sitter.

Detects declaration constructs in Rust source code:
- const/static arrays of struct literals (CONST_TABLE)
- Value-only enum variants (ENUM_DECLARATION)
- Struct definitions (TYPE_DEFINITION)
"""

from __future__ import annotations


from eigenhelm.declarations.models import DeclarationRegion, DeclarationType


def detect(source: str) -> tuple[DeclarationRegion, ...]:
    """Detect Rust declaration constructs.

    Finds const/static tables, value-only enums, and struct definitions
    by walking the AST for relevant node types.

    Returns:
        Sorted DeclarationRegion entries.
    """
    from eigenhelm.parsers.tree_sitter import parse_source

    root = parse_source(source, "rust")
    if root is None:
        return ()

    source_lines = source.splitlines()
    regions: list[DeclarationRegion] = []

    for node in root.children:
        if node.type in ("const_item", "static_item"):
            region = _detect_const_table(node, source_lines)
            if region is not None:
                regions.append(region)
        elif node.type == "enum_item":
            region = _detect_value_enum(node, source_lines)
            if region is not None:
                regions.append(region)
        elif node.type == "struct_item":
            region = _detect_struct(node, source_lines)
            if region is not None:
                regions.append(region)

    regions.sort(key=lambda r: r.start_line)
    return tuple(regions)


def _detect_const_table(node, source_lines: list[str]) -> DeclarationRegion | None:
    """Detect const/static items whose value is an array of struct literals."""
    # Find the value expression — look for array_expression containing struct_expression
    value_node = _find_child_by_type(node, "array_expression")
    if value_node is None:
        # The value might be a reference_expression wrapping an array: &[T{...}, ...]
        ref_node = _find_child_by_type(node, "reference_expression")
        if ref_node is not None:
            value_node = _find_child_by_type(ref_node, "array_expression")
    if value_node is None:
        return None

    # Check that the array contains at least one struct expression
    has_struct = any(child.type == "struct_expression" for child in value_node.children)
    if not has_struct:
        return None

    name = _extract_name(node)
    start_line = node.start_point[0] + 1
    end_line = node.end_point[0] + 1
    decl_count = _count_non_blank_lines(source_lines, start_line, end_line)

    return DeclarationRegion(
        declaration_type=DeclarationType.CONST_TABLE,
        start_line=start_line,
        end_line=end_line,
        declaration_line_count=decl_count,
        language="rust",
        node_name=name,
    )


def _detect_value_enum(node, source_lines: list[str]) -> DeclarationRegion | None:
    """Detect enums where all variants are simple (no tuple/struct data)."""
    variant_list = _find_child_by_type(node, "enum_variant_list")
    if variant_list is None:
        return None

    for child in variant_list.children:
        if child.type == "enum_variant":
            # A variant with complex data has field_declaration_list or
            # ordered_field_declaration_list children (tuple/struct variants)
            for vc in child.children:
                if vc.type in (
                    "field_declaration_list",
                    "ordered_field_declaration_list",
                ):
                    return None

    name = _extract_name(node)
    start_line = node.start_point[0] + 1
    end_line = node.end_point[0] + 1
    decl_count = _count_non_blank_lines(source_lines, start_line, end_line)

    return DeclarationRegion(
        declaration_type=DeclarationType.ENUM_DECLARATION,
        start_line=start_line,
        end_line=end_line,
        declaration_line_count=decl_count,
        language="rust",
        node_name=name,
    )


def _detect_struct(node, source_lines: list[str]) -> DeclarationRegion | None:
    """Detect struct definitions (the definition itself, not impl blocks)."""
    name = _extract_name(node)
    start_line = node.start_point[0] + 1
    end_line = node.end_point[0] + 1
    decl_count = _count_non_blank_lines(source_lines, start_line, end_line)

    return DeclarationRegion(
        declaration_type=DeclarationType.TYPE_DEFINITION,
        start_line=start_line,
        end_line=end_line,
        declaration_line_count=decl_count,
        language="rust",
        node_name=name,
    )


def _extract_name(node) -> str:
    """Extract the identifier name from a const/static/enum/struct node."""
    for child in node.children:
        if child.type in ("identifier", "type_identifier"):
            text = child.text
            if text is not None:
                return text.decode("utf-8") if isinstance(text, bytes) else text
    return "<anonymous>"


def _find_child_by_type(node, type_name: str):
    """Find the first direct child with the given node type."""
    for child in node.children:
        if child.type == type_name:
            return child
    return None


def _count_non_blank_lines(
    source_lines: list[str], start_line: int, end_line: int
) -> int:
    """Count non-blank lines within a 1-indexed inclusive line range."""
    count = 0
    for i in range(start_line - 1, min(end_line, len(source_lines))):
        if source_lines[i].strip():
            count += 1
    return max(count, 1)

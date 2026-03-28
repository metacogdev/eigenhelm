"""Python declaration detection via tree-sitter.

Detects declaration constructs: dataclasses, Protocol, TypedDict, NamedTuple,
Enum, Pydantic BaseModel, and module-level const tables.
"""

from __future__ import annotations

from eigenhelm.declarations.models import DeclarationRegion, DeclarationType


_DATACLASS_NAMES = frozenset({"dataclass", "dataclasses.dataclass"})

_PROTOCOL_BASES = frozenset({"Protocol"})
_TYPEDDICT_BASES = frozenset({"TypedDict"})
_NAMEDTUPLE_BASES = frozenset({"NamedTuple"})
_ENUM_BASES = frozenset({"Enum", "IntEnum", "StrEnum"})
_BASEMODEL_BASES = frozenset({"BaseModel"})


def detect(source: str) -> tuple[DeclarationRegion, ...]:
    """Detect Python declaration constructs in source code."""
    from eigenhelm.parsers.tree_sitter import parse_source

    root = parse_source(source, "python")
    if root is None:
        return ()

    regions: list[DeclarationRegion] = []

    for node in root.children:
        if node.type == "class_definition":
            _try_class(node, node, source, regions)
        elif node.type == "decorated_definition":
            inner = _get_inner_class(node)
            if inner is not None:
                _try_class(inner, node, source, regions)
        elif node.type in ("assignment", "expression_statement"):
            _try_const_table(node, source, regions)

    regions.sort(key=lambda r: r.start_line)
    return tuple(regions)


# ---------------------------------------------------------------------------
# Class analysis
# ---------------------------------------------------------------------------


def _try_class(
    class_node,
    span_node,
    source: str,
    regions: list[DeclarationRegion],
) -> None:
    bases = _get_base_names(class_node)
    decorators = _get_decorator_names(span_node)
    body = _get_body(class_node)
    if body is None:
        return

    name = _extract_name(class_node)

    if _is_dataclass_decorated(decorators):
        if _body_is_field_only(body):
            regions.append(
                _make_region(
                    DeclarationType.TYPE_DEFINITION,
                    span_node,
                    name,
                    source,
                    body,
                    count_fn=_count_field_lines,
                )
            )
        return

    if bases & _PROTOCOL_BASES:
        if _body_is_protocol(body):
            regions.append(
                _make_region(
                    DeclarationType.TYPE_DEFINITION,
                    span_node,
                    name,
                    source,
                    body,
                    count_fn=_count_protocol_lines,
                )
            )
        return

    if bases & _TYPEDDICT_BASES:
        if _body_is_field_only(body):
            regions.append(
                _make_region(
                    DeclarationType.TYPE_DEFINITION,
                    span_node,
                    name,
                    source,
                    body,
                    count_fn=_count_field_lines,
                )
            )
        return

    if bases & _NAMEDTUPLE_BASES:
        if _body_is_field_only(body):
            regions.append(
                _make_region(
                    DeclarationType.TYPE_DEFINITION,
                    span_node,
                    name,
                    source,
                    body,
                    count_fn=_count_field_lines,
                )
            )
        return

    if bases & _ENUM_BASES:
        if _body_is_enum(body):
            regions.append(
                _make_region(
                    DeclarationType.ENUM_DECLARATION,
                    span_node,
                    name,
                    source,
                    body,
                    count_fn=_count_assignment_lines,
                )
            )
        return

    if bases & _BASEMODEL_BASES:
        if _body_is_field_only(body):
            regions.append(
                _make_region(
                    DeclarationType.CONFIG_MODEL,
                    span_node,
                    name,
                    source,
                    body,
                    count_fn=_count_field_lines,
                )
            )
        return


def _make_region(
    decl_type: DeclarationType,
    span_node,
    name: str,
    source: str,
    body,
    count_fn,
) -> DeclarationRegion:
    start_line = span_node.start_point[0] + 1
    end_line = span_node.end_point[0] + 1
    decl_count = _count_decorator_and_header_lines(span_node) + count_fn(body, source)

    return DeclarationRegion(
        declaration_type=decl_type,
        start_line=start_line,
        end_line=end_line,
        declaration_line_count=decl_count,
        language="python",
        node_name=name,
    )


# ---------------------------------------------------------------------------
# Body classification helpers
# ---------------------------------------------------------------------------


def _is_annotation_or_field(node) -> bool:
    # Direct assignment node with type annotation: `x: int` or `x: int = 5`
    if node.type == "assignment":
        return _has_type_child(node)
    # expression_statement wrapping an assignment or type
    if node.type == "expression_statement":
        inner = node.children[0] if node.children else None
        if inner is None:
            return False
        if inner.type == "assignment" and _has_type_child(inner):
            return True
        if inner.type == "type":
            return True
        if inner.type == "ellipsis":
            return True
    return False


def _is_value_assignment(node) -> bool:
    # Assignment without type annotation: `RED = 1`
    if node.type == "assignment":
        return not _has_type_child(node)
    if node.type == "expression_statement":
        inner = node.children[0] if node.children else None
        if inner is not None and inner.type == "assignment":
            return not _has_type_child(inner)
    return False


def _has_type_child(assignment_node) -> bool:
    return any(c.type == "type" for c in assignment_node.children)


def _body_is_field_only(body) -> bool:
    for child in body.children:
        if _is_ignorable(child):
            continue
        if _is_annotation_or_field(child):
            continue
        if _is_value_assignment(child):
            # Allow plain assignments in field-only (e.g. default values)
            continue
        if child.type == "pass_statement":
            continue
        if child.type == "expression_statement":
            inner = child.children[0] if child.children else None
            if inner is not None and inner.type in ("ellipsis", "string"):
                continue
        return False
    return True


def _body_is_protocol(body) -> bool:
    for child in body.children:
        if _is_ignorable(child):
            continue
        if _is_annotation_or_field(child):
            continue
        if child.type == "pass_statement":
            continue
        if child.type == "function_definition":
            if not _is_stub_method(child):
                return False
            continue
        if child.type == "decorated_definition":
            fn = _get_inner_function(child)
            if fn is None or not _is_stub_method(fn):
                return False
            continue
        if child.type == "expression_statement":
            inner = child.children[0] if child.children else None
            if inner is not None and inner.type == "ellipsis":
                continue
        return False
    return True


def _body_is_enum(body) -> bool:
    for child in body.children:
        if _is_ignorable(child):
            continue
        if _is_value_assignment(child):
            continue
        if child.type == "pass_statement":
            continue
        if child.type == "expression_statement":
            inner = child.children[0] if child.children else None
            if inner is not None and inner.type == "ellipsis":
                continue
        return False
    return True


def _is_stub_method(fn_node) -> bool:
    body = _get_body(fn_node)
    if body is None:
        return False
    for child in body.children:
        if _is_ignorable(child):
            continue
        if child.type == "ellipsis":
            continue
        if child.type == "expression_statement":
            inner = child.children[0] if child.children else None
            if inner is not None and inner.type == "ellipsis":
                continue
            return False
        if child.type == "pass_statement":
            continue
        return False
    return True


def _is_ignorable(node) -> bool:
    return node.type in ("comment", "newline", "NEWLINE", "INDENT", "DEDENT", "string")


# ---------------------------------------------------------------------------
# Line counting helpers
# ---------------------------------------------------------------------------


def _count_decorator_and_header_lines(span_node) -> int:
    if span_node.type == "decorated_definition":
        count = 0
        for child in span_node.children:
            if child.type == "decorator":
                count += child.end_point[0] - child.start_point[0] + 1
            elif child.type == "class_definition":
                count += 1
                break
        return count
    return 1


def _count_field_lines(body, source: str) -> int:
    count = 0
    for child in body.children:
        if _is_ignorable(child):
            continue
        if _is_annotation_or_field(child) or _is_value_assignment(child):
            count += _non_blank_line_count(child, source)
        elif child.type == "pass_statement":
            count += 1
    return count


def _count_protocol_lines(body, source: str) -> int:
    count = 0
    for child in body.children:
        if _is_ignorable(child):
            continue
        if _is_annotation_or_field(child):
            count += _non_blank_line_count(child, source)
        elif child.type == "pass_statement":
            count += 1
        elif child.type == "function_definition":
            count += _count_stub_method_lines(child)
        elif child.type == "decorated_definition":
            fn = _get_inner_function(child)
            if fn is not None:
                for dec_child in child.children:
                    if dec_child.type == "decorator":
                        count += dec_child.end_point[0] - dec_child.start_point[0] + 1
                count += _count_stub_method_lines(fn)
    return count


def _count_stub_method_lines(fn_node) -> int:
    # Count unique non-blank lines spanning the stub method
    lines: set[int] = set()
    # The def signature line
    lines.add(fn_node.start_point[0])
    fn_body = _get_body(fn_node)
    if fn_body is not None:
        for child in fn_body.children:
            if _is_ignorable(child):
                continue
            if child.type in ("ellipsis", "pass_statement"):
                lines.add(child.start_point[0])
            elif child.type == "expression_statement":
                inner = child.children[0] if child.children else None
                if inner is not None and inner.type == "ellipsis":
                    lines.add(child.start_point[0])
    return len(lines)


def _count_assignment_lines(body, source: str) -> int:
    count = 0
    for child in body.children:
        if _is_ignorable(child):
            continue
        if _is_value_assignment(child):
            count += _non_blank_line_count(child, source)
        elif child.type == "pass_statement":
            count += 1
    return count


def _non_blank_line_count(node, source: str) -> int:
    start = node.start_point[0]
    end = node.end_point[0]
    lines = source.splitlines()[start : end + 1]
    return sum(1 for line in lines if line.strip())


# ---------------------------------------------------------------------------
# Const table detection
# ---------------------------------------------------------------------------


def _try_const_table(node, source: str, regions: list[DeclarationRegion]) -> None:
    # Handle both top-level `assignment` and `expression_statement` wrapping assignment
    assign_node = node
    if node.type == "expression_statement":
        if not node.children:
            return
        assign_node = node.children[0]
    if assign_node.type != "assignment":
        return

    name_node = None
    value_node = None
    for child in assign_node.children:
        if child.type == "identifier" and name_node is None:
            name_node = child
        elif child.type in ("list", "tuple"):
            value_node = child

    if name_node is None or value_node is None:
        return

    name = _text(name_node)
    if not name or name != name.upper() or not name.replace("_", "").isalpha():
        return

    if not _is_literal_collection(value_node):
        return

    start_line = node.start_point[0] + 1
    end_line = node.end_point[0] + 1
    decl_lines = _non_blank_line_count(node, source)

    regions.append(
        DeclarationRegion(
            declaration_type=DeclarationType.CONST_TABLE,
            start_line=start_line,
            end_line=end_line,
            declaration_line_count=decl_lines,
            language="python",
            node_name=name,
        )
    )


def _is_literal_collection(node) -> bool:
    elements = [c for c in node.children if c.type not in (",", "[", "]", "(", ")")]
    if not elements:
        return False
    return all(c.type in ("dictionary",) for c in elements)


# ---------------------------------------------------------------------------
# AST navigation helpers
# ---------------------------------------------------------------------------


def _get_base_names(class_node) -> frozenset[str]:
    names: set[str] = set()
    for child in class_node.children:
        if child.type == "argument_list":
            for arg in child.children:
                if arg.type == "identifier":
                    t = _text(arg)
                    if t:
                        names.add(t)
                elif arg.type == "attribute":
                    # For qualified names like typing.Protocol, extract
                    # both the full name and the rightmost identifier
                    t = _text(arg)
                    if t:
                        names.add(t)
                        # Also add the bare name (e.g., "Protocol" from "typing.Protocol")
                        parts = t.split(".")
                        if len(parts) > 1:
                            names.add(parts[-1])
    return frozenset(names)


def _get_decorator_names(node) -> frozenset[str]:
    names: set[str] = set()
    if node.type != "decorated_definition":
        return frozenset()
    for child in node.children:
        if child.type == "decorator":
            name = _extract_decorator_name(child)
            if name:
                names.add(name)
    return frozenset(names)


def _extract_decorator_name(decorator_node) -> str:
    for child in decorator_node.children:
        if child.type == "identifier":
            return _text(child)
        if child.type == "call":
            for call_child in child.children:
                if call_child.type == "identifier":
                    return _text(call_child)
                if call_child.type == "attribute":
                    return _text(call_child)
        if child.type == "attribute":
            return _text(child)
    return ""


def _get_body(node):
    for child in node.children:
        if child.type == "block":
            return child
    return None


def _get_inner_class(node):
    for child in node.children:
        if child.type == "class_definition":
            return child
    return None


def _get_inner_function(node):
    for child in node.children:
        if child.type == "function_definition":
            return child
    return None


def _extract_name(node) -> str:
    for child in node.children:
        if child.type == "identifier":
            return _text(child)
    return ""


def _text(node) -> str:
    t = node.text
    if t is None:
        return ""
    return t.decode("utf-8") if isinstance(t, bytes) else t


def _is_dataclass_decorated(decorators: frozenset[str]) -> bool:
    return bool(decorators & _DATACLASS_NAMES)

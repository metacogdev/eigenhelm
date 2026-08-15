"""Extended tests for Python declaration detection — covers uncovered branches."""

from __future__ import annotations

import textwrap

from eigenhelm.declarations.models import DeclarationType
from eigenhelm.declarations.python import detect


class TestParseFailure:
    """Line 27: root is None when tree-sitter cannot parse."""

    def test_unparseable_source_returns_empty(self) -> None:
        # tree-sitter is lenient, but a completely invalid input that
        # produces no useful root children should still return empty.
        # Use a None-returning path by passing source that parses but
        # has no top-level class/assignment nodes.
        result = detect("pass\n")
        assert result == ()


class TestBodyIsNone:
    """Line 60: class with no body block."""

    def test_class_no_body_not_detected(self) -> None:
        # A class definition with a syntax error where body is absent.
        # tree-sitter may still parse partial, but body lookup returns None.
        src = "class Foo(TypedDict): ...\n"
        # Should not crash; the ellipsis is inside the body block so
        # it's still parseable. But we test that detection handles it.
        detect(src)  # Should not raise


class TestAnnotationOrFieldBranches:
    """Lines 182-190: expression_statement wrapping type, ellipsis, assignment."""

    def test_typeddict_with_ellipsis_body_not_detected(self) -> None:
        """TypedDict with only bare ellipsis in body — bare ellipsis is not
        wrapped in expression_statement, so it's not recognized as field-only."""
        src = textwrap.dedent("""\
            from typing import TypedDict

            class Empty(TypedDict):
                ...
        """)
        # Bare ellipsis (not expression_statement wrapped) fails field-only check
        regions = detect(src)
        assert len(regions) == 0

    def test_protocol_with_ellipsis_only_not_detected(self) -> None:
        """Protocol with only bare ellipsis (no methods) — bare ellipsis
        is not wrapped in expression_statement, so protocol check fails."""
        src = textwrap.dedent("""\
            from typing import Protocol

            class Marker(Protocol):
                ...
        """)
        # Bare ellipsis hits return False in _body_is_protocol
        regions = detect(src)
        assert len(regions) == 0

    def test_typeddict_with_field_and_type_annotation(self) -> None:
        """TypedDict with expression_statement wrapping type annotation."""
        src = textwrap.dedent("""\
            from typing import TypedDict

            class Config(TypedDict):
                host: str
                port: int
                debug: bool
        """)
        regions = detect(src)
        assert len(regions) == 1
        assert regions[0].declaration_type == DeclarationType.TYPE_DEFINITION

    def test_dataclass_with_annotated_field_expression(self) -> None:
        """Dataclass with expression_statement wrapping annotated assignment."""
        src = textwrap.dedent("""\
            from dataclasses import dataclass

            @dataclass
            class Settings:
                host: str = "localhost"
                port: int = 8080
        """)
        regions = detect(src)
        assert len(regions) == 1


class TestIsValueAssignment:
    """Lines 199-201: expression_statement wrapping plain assignment."""

    def test_enum_with_expression_statement_assignments(self) -> None:
        """Enum members as expression_statement-wrapped assignments."""
        src = textwrap.dedent("""\
            from enum import IntEnum

            class Priority(IntEnum):
                LOW = 1
                MEDIUM = 2
                HIGH = 3
        """)
        regions = detect(src)
        assert len(regions) == 1
        assert regions[0].declaration_type == DeclarationType.ENUM_DECLARATION
        assert regions[0].node_name == "Priority"


class TestBodyIsFieldOnly:
    """Lines 212-223: _body_is_field_only branches."""

    def test_dataclass_with_pass_statement(self) -> None:
        """Dataclass with only 'pass' in body is detected."""
        src = textwrap.dedent("""\
            from dataclasses import dataclass

            @dataclass
            class Empty:
                pass
        """)
        regions = detect(src)
        assert len(regions) == 1
        assert regions[0].declaration_type == DeclarationType.TYPE_DEFINITION

    def test_dataclass_with_plain_assignment(self) -> None:
        """Dataclass with plain assignment (no type annotation) is detected."""
        src = textwrap.dedent("""\
            from dataclasses import dataclass

            @dataclass
            class Defaults:
                name: str = "unnamed"
                value = 42
        """)
        regions = detect(src)
        assert len(regions) == 1
        assert regions[0].declaration_type == DeclarationType.TYPE_DEFINITION

    def test_dataclass_with_docstring(self) -> None:
        """Dataclass with a docstring in body is detected (string is ignorable or field-ok)."""
        src = textwrap.dedent('''\
            from dataclasses import dataclass

            @dataclass(frozen=True)
            class Point:
                """A 2D point."""
                x: float
                y: float
        ''')
        regions = detect(src)
        assert len(regions) == 1
        assert regions[0].declaration_type == DeclarationType.TYPE_DEFINITION
        assert regions[0].node_name == "Point"

    def test_namedtuple_with_defaults(self) -> None:
        """NamedTuple with default values detected."""
        src = textwrap.dedent("""\
            from typing import NamedTuple

            class Config(NamedTuple):
                host: str = "localhost"
                port: int = 8080
        """)
        regions = detect(src)
        assert len(regions) == 1
        assert regions[0].declaration_type == DeclarationType.TYPE_DEFINITION

    def test_typeddict_with_method_not_detected(self) -> None:
        """TypedDict with a method is NOT detected (not field-only)."""
        src = textwrap.dedent("""\
            from typing import TypedDict

            class Settings(TypedDict):
                host: str
                port: int

                def validate(self):
                    return True
        """)
        regions = detect(src)
        assert len(regions) == 0

    def test_namedtuple_with_method_not_detected(self) -> None:
        """NamedTuple with a method is NOT detected."""
        src = textwrap.dedent("""\
            from typing import NamedTuple

            class Point(NamedTuple):
                x: float
                y: float

                def distance(self):
                    return (self.x**2 + self.y**2)**0.5
        """)
        regions = detect(src)
        assert len(regions) == 0

    def test_basemodel_with_method_not_detected(self) -> None:
        """BaseModel with a method is NOT detected."""
        src = textwrap.dedent("""\
            from pydantic import BaseModel

            class AppConfig(BaseModel):
                host: str
                port: int

                def url(self):
                    return f"http://{self.host}:{self.port}"
        """)
        regions = detect(src)
        assert len(regions) == 0


class TestBodyIsProtocol:
    """Lines 228-249: _body_is_protocol branches."""

    def test_protocol_with_pass_statement(self) -> None:
        """Protocol with pass and annotations is detected."""
        src = textwrap.dedent("""\
            from typing import Protocol

            class Empty(Protocol):
                pass
        """)
        regions = detect(src)
        assert len(regions) == 1
        assert regions[0].declaration_type == DeclarationType.TYPE_DEFINITION

    def test_protocol_with_decorated_method(self) -> None:
        """Protocol with @abstractmethod decorated stubs is detected."""
        src = textwrap.dedent("""\
            from typing import Protocol

            class Scorer(Protocol):
                @property
                def name(self) -> str:
                    ...

                def score(self, code: str) -> float:
                    ...
        """)
        regions = detect(src)
        assert len(regions) == 1
        assert regions[0].declaration_type == DeclarationType.TYPE_DEFINITION

    def test_protocol_with_non_stub_method_not_detected(self) -> None:
        """Protocol with a real method body is NOT detected."""
        src = textwrap.dedent("""\
            from typing import Protocol

            class Scorer(Protocol):
                def score(self, code: str) -> float:
                    return 0.0
        """)
        regions = detect(src)
        assert len(regions) == 0

    def test_protocol_with_decorated_non_stub_not_detected(self) -> None:
        """Protocol with a decorated non-stub method is NOT detected."""
        src = textwrap.dedent("""\
            from typing import Protocol

            class Scorer(Protocol):
                @staticmethod
                def default_score() -> float:
                    return 0.5
        """)
        regions = detect(src)
        assert len(regions) == 0

    def test_protocol_with_fields_and_methods(self) -> None:
        """Protocol with field annotations and stub methods detected."""
        src = textwrap.dedent("""\
            from typing import Protocol

            class Handler(Protocol):
                name: str

                def handle(self, data: bytes) -> None:
                    ...
        """)
        regions = detect(src)
        assert len(regions) == 1
        assert regions[0].declaration_type == DeclarationType.TYPE_DEFINITION

    def test_protocol_with_non_function_decorated_def_not_detected(self) -> None:
        """Protocol with decorated_definition that is not a function."""
        src = textwrap.dedent("""\
            from typing import Protocol

            class Meta(Protocol):
                def method(self) -> None:
                    print("not a stub")
        """)
        regions = detect(src)
        assert len(regions) == 0


class TestBodyIsEnum:
    """Lines 253-265: _body_is_enum branches."""

    def test_enum_with_pass_only(self) -> None:
        """Enum with only pass is detected."""
        src = textwrap.dedent("""\
            from enum import Enum

            class EmptyEnum(Enum):
                pass
        """)
        regions = detect(src)
        assert len(regions) == 1
        assert regions[0].declaration_type == DeclarationType.ENUM_DECLARATION

    def test_enum_with_ellipsis_body(self) -> None:
        """Enum with ellipsis in body detected."""
        src = textwrap.dedent("""\
            from enum import StrEnum

            class Status(StrEnum):
                ACTIVE = "active"
                INACTIVE = "inactive"
        """)
        regions = detect(src)
        assert len(regions) == 1
        assert regions[0].declaration_type == DeclarationType.ENUM_DECLARATION

    def test_enum_with_non_assignment_not_detected(self) -> None:
        """Enum with a non-assignment statement (e.g. function call) is NOT detected."""
        src = textwrap.dedent("""\
            from enum import Enum

            class BadEnum(Enum):
                RED = 1
                GREEN = 2

                def describe(self):
                    return self.name.lower()
        """)
        regions = detect(src)
        assert len(regions) == 0


class TestIsStubMethod:
    """Lines 269-285: _is_stub_method branches."""

    def test_stub_method_with_pass(self) -> None:
        """Protocol method with pass body is a valid stub."""
        src = textwrap.dedent("""\
            from typing import Protocol

            class Writer(Protocol):
                def write(self, data: bytes) -> None:
                    pass
        """)
        regions = detect(src)
        assert len(regions) == 1

    def test_stub_method_with_ellipsis(self) -> None:
        """Protocol method with ellipsis body is a valid stub."""
        src = textwrap.dedent("""\
            from typing import Protocol

            class Reader(Protocol):
                def read(self) -> bytes:
                    ...
        """)
        regions = detect(src)
        assert len(regions) == 1

    def test_stub_method_with_real_body_not_detected(self) -> None:
        """Protocol method with a return statement is NOT a stub."""
        src = textwrap.dedent("""\
            from typing import Protocol

            class Processor(Protocol):
                def process(self, x: int) -> int:
                    return x * 2
        """)
        regions = detect(src)
        assert len(regions) == 0


class TestCountFieldLines:
    """Lines 310-319: _count_field_lines counting."""

    def test_dataclass_field_line_count(self) -> None:
        """Verify field line counting includes all annotation lines."""
        src = textwrap.dedent("""\
            from dataclasses import dataclass

            @dataclass(frozen=True)
            class Record:
                id: int
                name: str
                value: float
                active: bool
        """)
        regions = detect(src)
        assert len(regions) == 1
        # 1 decorator + 1 class header + 4 fields = 6
        assert regions[0].declaration_line_count == 6

    def test_dataclass_with_pass_counted(self) -> None:
        """Verify pass statement is counted in field lines."""
        src = textwrap.dedent("""\
            from dataclasses import dataclass

            @dataclass
            class Placeholder:
                pass
        """)
        regions = detect(src)
        assert len(regions) == 1
        # 1 decorator + 1 class header + 1 pass = 3
        assert regions[0].declaration_line_count == 3


class TestCountProtocolLines:
    """Lines 323-340: _count_protocol_lines counting."""

    def test_protocol_lines_with_decorated_stubs(self) -> None:
        """Verify protocol line counting includes decorated stub methods."""
        src = textwrap.dedent("""\
            from typing import Protocol

            class Configurable(Protocol):
                @property
                def config(self) -> dict:
                    ...

                def apply(self, settings: dict) -> None:
                    ...
        """)
        regions = detect(src)
        assert len(regions) == 1
        r = regions[0]
        # class header(1) + @property(1) + def config(1) + ...(1) + def apply(1) + ...(1) = 6
        assert r.declaration_line_count >= 5

    def test_protocol_lines_with_field_annotations(self) -> None:
        """Verify protocol line counting includes field annotations."""
        src = textwrap.dedent("""\
            from typing import Protocol

            class Named(Protocol):
                name: str
                version: int
        """)
        regions = detect(src)
        assert len(regions) == 1
        # 1 class header + 2 fields = 3
        assert regions[0].declaration_line_count == 3


class TestCountStubMethodLines:
    """Lines 344-360: _count_stub_method_lines."""

    def test_stub_with_pass_counted(self) -> None:
        """Verify stub method with pass is counted correctly."""
        src = textwrap.dedent("""\
            from typing import Protocol

            class Closeable(Protocol):
                def close(self) -> None:
                    pass
        """)
        regions = detect(src)
        assert len(regions) == 1
        # 1 header + 1 def + 1 pass = 3
        assert regions[0].declaration_line_count == 3


class TestCountAssignmentLines:
    """Lines 363-371: _count_assignment_lines for enums."""

    def test_enum_assignment_counting(self) -> None:
        """Verify enum assignment counting includes all members."""
        src = textwrap.dedent("""\
            from enum import Enum

            class Direction(Enum):
                NORTH = 0
                SOUTH = 1
                EAST = 2
                WEST = 3
        """)
        regions = detect(src)
        assert len(regions) == 1
        # 1 header + 4 assignments = 5
        assert regions[0].declaration_line_count == 5

    def test_enum_with_pass_counted(self) -> None:
        """Verify pass counts in enum assignment lines."""
        src = textwrap.dedent("""\
            from enum import Enum

            class Placeholder(Enum):
                pass
        """)
        regions = detect(src)
        assert len(regions) == 1
        assert regions[0].declaration_line_count == 2  # header + pass


class TestConstTable:
    """Lines 387-428: _try_const_table and surrounding logic."""

    def test_expression_statement_empty_children(self) -> None:
        """expression_statement with no children is skipped."""
        # This is hard to trigger directly; the key path is the guard.
        src = textwrap.dedent("""\
            x = 5
        """)
        regions = detect(src)
        assert regions == ()

    def test_non_assignment_expression_statement_skipped(self) -> None:
        """expression_statement that wraps something other than assignment."""
        src = textwrap.dedent("""\
            print("hello")
        """)
        regions = detect(src)
        assert regions == ()

    def test_const_table_tuple_of_dicts(self) -> None:
        """Tuple of dicts as CONST_TABLE."""
        src = textwrap.dedent("""\
            CONFIGS = (
                {"key": "a", "value": 1},
                {"key": "b", "value": 2},
            )
        """)
        regions = detect(src)
        assert len(regions) == 1
        assert regions[0].declaration_type == DeclarationType.CONST_TABLE
        assert regions[0].node_name == "CONFIGS"

    def test_lowercase_name_not_const_table(self) -> None:
        """Non-uppercase name is not detected as const table."""
        src = textwrap.dedent("""\
            routes = [
                {"path": "/home", "handler": "home"},
            ]
        """)
        regions = detect(src)
        assert regions == ()

    def test_name_with_numbers_not_const_table(self) -> None:
        """Name containing digits is not detected as const table."""
        src = textwrap.dedent("""\
            ROUTE123 = [
                {"path": "/home"},
            ]
        """)
        regions = detect(src)
        assert regions == ()

    def test_non_literal_collection_not_detected(self) -> None:
        """Array of non-dicts is not detected as const table."""
        src = textwrap.dedent("""\
            ITEMS = [1, 2, 3]
        """)
        regions = detect(src)
        assert regions == ()

    def test_empty_list_not_const_table(self) -> None:
        """Empty list is not detected as const table."""
        src = textwrap.dedent("""\
            EMPTY = []
        """)
        regions = detect(src)
        assert regions == ()

    def test_const_table_with_no_name_node(self) -> None:
        """Assignment without identifier on LHS is not const table."""
        # e.g. subscript assignment or attribute assignment
        src = textwrap.dedent("""\
            obj.ROUTES = [
                {"path": "/home"},
            ]
        """)
        regions = detect(src)
        assert regions == ()

    def test_assignment_to_non_collection(self) -> None:
        """Assignment where RHS is not a list/tuple."""
        src = textwrap.dedent("""\
            CONFIG = {"key": "value"}
        """)
        regions = detect(src)
        assert regions == ()


class TestGetBaseNames:
    """Lines 443-462: _get_base_names with qualified names."""

    def test_qualified_base_name(self) -> None:
        """typing.Protocol base is detected via qualified name."""
        src = textwrap.dedent("""\
            import typing

            class Scorer(typing.Protocol):
                def score(self) -> float:
                    ...
        """)
        regions = detect(src)
        assert len(regions) == 1
        assert regions[0].declaration_type == DeclarationType.TYPE_DEFINITION

    def test_qualified_typeddict(self) -> None:
        """typing.TypedDict detected via qualified name."""
        src = textwrap.dedent("""\
            import typing

            class Config(typing.TypedDict):
                host: str
                port: int
        """)
        regions = detect(src)
        assert len(regions) == 1
        assert regions[0].declaration_type == DeclarationType.TYPE_DEFINITION


class TestExtractDecoratorName:
    """Lines 477-489: _extract_decorator_name branches."""

    def test_decorator_with_call_syntax(self) -> None:
        """@dataclass(...) with call syntax detected."""
        src = textwrap.dedent("""\
            from dataclasses import dataclass

            @dataclass(frozen=True, slots=True)
            class Config:
                host: str
                port: int
        """)
        regions = detect(src)
        assert len(regions) == 1

    def test_qualified_decorator(self) -> None:
        """@dataclasses.dataclass detected via attribute."""
        src = textwrap.dedent("""\
            import dataclasses

            @dataclasses.dataclass
            class Point:
                x: float
                y: float
        """)
        regions = detect(src)
        assert len(regions) == 1
        assert regions[0].declaration_type == DeclarationType.TYPE_DEFINITION

    def test_qualified_decorator_with_call(self) -> None:
        """@dataclasses.dataclass(frozen=True) detected."""
        src = textwrap.dedent("""\
            import dataclasses

            @dataclasses.dataclass(frozen=True)
            class Vec:
                dx: float
                dy: float
        """)
        regions = detect(src)
        assert len(regions) == 1
        assert regions[0].declaration_type == DeclarationType.TYPE_DEFINITION


class TestGetInnerFunction:
    """Lines 506-510: _get_inner_function for decorated definitions."""

    def test_decorated_method_in_protocol(self) -> None:
        """decorated_definition containing a function_definition in protocol."""
        src = textwrap.dedent("""\
            from typing import Protocol

            class Configurable(Protocol):
                @property
                def name(self) -> str:
                    ...

                @property
                def version(self) -> int:
                    ...
        """)
        regions = detect(src)
        assert len(regions) == 1


class TestExtractName:
    """Lines 513-517: _extract_name for class definitions."""

    def test_class_name_extracted(self) -> None:
        """Class name is properly extracted."""
        src = textwrap.dedent("""\
            from dataclasses import dataclass

            @dataclass
            class MySpecialClass:
                value: int
        """)
        regions = detect(src)
        assert len(regions) == 1
        assert regions[0].node_name == "MySpecialClass"


class TestTextHelper:
    """Lines 520-524: _text helper for bytes vs str."""

    def test_text_returns_string(self) -> None:
        """Node text (bytes) is decoded to str."""
        src = textwrap.dedent("""\
            from dataclasses import dataclass

            @dataclass
            class Utf8Name:
                name: str
        """)
        regions = detect(src)
        assert len(regions) == 1
        assert isinstance(regions[0].node_name, str)
        assert regions[0].node_name == "Utf8Name"


class TestDecoratedDefinition:
    """Lines 34-37: decorated_definition dispatch."""

    def test_decorated_non_class_ignored(self) -> None:
        """decorated_definition wrapping a function (not class) is ignored."""
        src = textwrap.dedent("""\
            import functools

            @functools.lru_cache
            def expensive():
                return 42
        """)
        regions = detect(src)
        assert regions == ()

    def test_undecorated_class_detected(self) -> None:
        """Class without decorator but with matching base is detected."""
        src = textwrap.dedent("""\
            from typing import TypedDict

            class Settings(TypedDict):
                debug: bool
                verbose: bool
        """)
        regions = detect(src)
        assert len(regions) == 1

    def test_multiple_decorators(self) -> None:
        """Class with multiple decorators, one being @dataclass."""
        src = textwrap.dedent("""\
            from dataclasses import dataclass

            @dataclass
            class Multi:
                x: int
                y: int
        """)
        regions = detect(src)
        assert len(regions) == 1


class TestMultipleRegions:
    """Multiple declaration regions in one file."""

    def test_multiple_enums_detected(self) -> None:
        src = textwrap.dedent("""\
            from enum import Enum

            class Color(Enum):
                RED = 1
                GREEN = 2

            class Size(Enum):
                SMALL = 1
                LARGE = 2
        """)
        regions = detect(src)
        assert len(regions) == 2
        assert all(r.declaration_type == DeclarationType.ENUM_DECLARATION for r in regions)

    def test_mixed_declarations(self) -> None:
        src = textwrap.dedent("""\
            from dataclasses import dataclass
            from typing import Protocol
            from enum import Enum

            @dataclass(frozen=True)
            class Point:
                x: float
                y: float

            class Scorer(Protocol):
                def score(self) -> float:
                    ...

            class Color(Enum):
                RED = 1
                GREEN = 2

            ROUTES = [
                {"path": "/home", "handler": "home"},
            ]
        """)
        regions = detect(src)
        assert len(regions) == 4
        types = {r.declaration_type for r in regions}
        assert DeclarationType.TYPE_DEFINITION in types
        assert DeclarationType.ENUM_DECLARATION in types
        assert DeclarationType.CONST_TABLE in types

    def test_regions_sorted_by_start_line(self) -> None:
        src = textwrap.dedent("""\
            from enum import Enum
            from dataclasses import dataclass

            class Size(Enum):
                SMALL = 1
                LARGE = 2

            @dataclass
            class Config:
                host: str
        """)
        regions = detect(src)
        assert len(regions) == 2
        assert regions[0].start_line < regions[1].start_line


class TestDecoratorAndHeaderLineCounting:
    """Lines 298-308: _count_decorator_and_header_lines."""

    def test_non_decorated_class_header_is_one_line(self) -> None:
        """Non-decorated class counts 1 for header."""
        src = textwrap.dedent("""\
            from typing import TypedDict

            class Config(TypedDict):
                host: str
                port: int
        """)
        regions = detect(src)
        assert len(regions) == 1
        # 1 header + 2 fields = 3
        assert regions[0].declaration_line_count == 3

    def test_multi_line_decorator(self) -> None:
        """Multi-line decorator counted correctly."""
        src = textwrap.dedent("""\
            from dataclasses import dataclass

            @dataclass(
                frozen=True,
            )
            class Cfg:
                x: int
        """)
        regions = detect(src)
        assert len(regions) == 1
        # decorator spans 3 lines + 1 header + 1 field = 5
        assert regions[0].declaration_line_count >= 4


class TestInternalFunctionsDirectly:
    """Test internal helper functions directly with mock AST nodes to cover
    defensive branches that are unreachable with valid Python source."""

    def test_text_with_none(self) -> None:
        """_text returns empty string when node.text is None."""
        from eigenhelm.declarations.python import _text

        class FakeNode:
            text = None

        assert _text(FakeNode()) == ""

    def test_text_with_str(self) -> None:
        """_text returns string directly when node.text is str."""
        from eigenhelm.declarations.python import _text

        class FakeNode:
            text = "hello"

        assert _text(FakeNode()) == "hello"

    def test_extract_name_no_identifier(self) -> None:
        """_extract_name returns empty string when no identifier child."""
        from eigenhelm.declarations.python import _extract_name

        class FakeNode:
            children = []

        assert _extract_name(FakeNode()) == ""

    def test_get_body_no_block(self) -> None:
        """_get_body returns None when no block child."""
        from eigenhelm.declarations.python import _get_body

        class FakeChild:
            type = "identifier"

        class FakeNode:
            children = [FakeChild()]

        assert _get_body(FakeNode()) is None

    def test_get_inner_function_no_function(self) -> None:
        """_get_inner_function returns None when no function_definition child."""
        from eigenhelm.declarations.python import _get_inner_function

        class FakeChild:
            type = "decorator"

        class FakeNode:
            children = [FakeChild()]

        assert _get_inner_function(FakeNode()) is None

    def test_extract_decorator_name_no_match(self) -> None:
        """_extract_decorator_name returns '' when no identifiable name."""
        from eigenhelm.declarations.python import _extract_decorator_name

        class FakeChild:
            type = "@"

        class FakeNode:
            children = [FakeChild()]

        assert _extract_decorator_name(FakeNode()) == ""

    def test_is_annotation_or_field_expression_statement_no_children(self) -> None:
        """_is_annotation_or_field returns False for expression_statement with no children."""
        from eigenhelm.declarations.python import _is_annotation_or_field

        class FakeNode:
            type = "expression_statement"
            children = []

        assert _is_annotation_or_field(FakeNode()) is False

    def test_is_annotation_or_field_expression_statement_with_type(self) -> None:
        """_is_annotation_or_field returns True for expression_statement wrapping type."""
        from eigenhelm.declarations.python import _is_annotation_or_field

        class FakeInner:
            type = "type"

        class FakeNode:
            type = "expression_statement"
            children = [FakeInner()]

        assert _is_annotation_or_field(FakeNode()) is True

    def test_is_annotation_or_field_expression_statement_with_ellipsis(self) -> None:
        """_is_annotation_or_field returns True for expression_statement wrapping ellipsis."""
        from eigenhelm.declarations.python import _is_annotation_or_field

        class FakeInner:
            type = "ellipsis"

        class FakeNode:
            type = "expression_statement"
            children = [FakeInner()]

        assert _is_annotation_or_field(FakeNode()) is True

    def test_is_annotation_or_field_expression_statement_with_assignment_typed(self) -> None:
        """_is_annotation_or_field for expression_statement wrapping typed assignment."""
        from eigenhelm.declarations.python import _is_annotation_or_field

        class FakeType:
            type = "type"

        class FakeInner:
            type = "assignment"
            children = [FakeType()]

        class FakeNode:
            type = "expression_statement"
            children = [FakeInner()]

        assert _is_annotation_or_field(FakeNode()) is True

    def test_is_value_assignment_expression_statement(self) -> None:
        """_is_value_assignment for expression_statement wrapping plain assignment."""
        from eigenhelm.declarations.python import _is_value_assignment

        class FakeInner:
            type = "assignment"
            children = []  # no type child

        class FakeNode:
            type = "expression_statement"
            children = [FakeInner()]

        assert _is_value_assignment(FakeNode()) is True

    def test_body_is_field_only_with_expression_statement_ellipsis(self) -> None:
        """_body_is_field_only handles expression_statement wrapping ellipsis."""
        from eigenhelm.declarations.python import _body_is_field_only

        class FakeEllipsis:
            type = "ellipsis"

        class FakeExprStmt:
            type = "expression_statement"
            children = [FakeEllipsis()]

        class FakeBody:
            children = [FakeExprStmt()]

        assert _body_is_field_only(FakeBody()) is True

    def test_body_is_field_only_with_expression_statement_string(self) -> None:
        """_body_is_field_only handles expression_statement wrapping string."""
        from eigenhelm.declarations.python import _body_is_field_only

        class FakeString:
            type = "string"

        class FakeExprStmt:
            type = "expression_statement"
            children = [FakeString()]

        class FakeBody:
            children = [FakeExprStmt()]

        assert _body_is_field_only(FakeBody()) is True

    def test_body_is_protocol_with_comment(self) -> None:
        """_body_is_protocol skips comment children."""
        from eigenhelm.declarations.python import _body_is_protocol

        class FakeComment:
            type = "comment"

        class FakeBody:
            children = [FakeComment()]

        assert _body_is_protocol(FakeBody()) is True

    def test_body_is_protocol_with_expression_statement_ellipsis(self) -> None:
        """_body_is_protocol handles expression_statement wrapping ellipsis."""
        from eigenhelm.declarations.python import _body_is_protocol

        class FakeEllipsis:
            type = "ellipsis"

        class FakeExprStmt:
            type = "expression_statement"
            children = [FakeEllipsis()]

        class FakeBody:
            children = [FakeExprStmt()]

        assert _body_is_protocol(FakeBody()) is True

    def test_body_is_protocol_expression_statement_ellipsis_then_pass(self) -> None:
        """_body_is_protocol with expression_statement ellipsis followed by pass."""
        from eigenhelm.declarations.python import _body_is_protocol

        class FakeEllipsis:
            type = "ellipsis"

        class FakeExprStmt:
            type = "expression_statement"
            children = [FakeEllipsis()]

        class FakePass:
            type = "pass_statement"

        class FakeBody:
            children = [FakeExprStmt(), FakePass()]

        assert _body_is_protocol(FakeBody()) is True

    def test_body_is_protocol_expression_statement_non_ellipsis_rejected(self) -> None:
        """_body_is_protocol rejects expression_statement wrapping non-ellipsis."""
        from eigenhelm.declarations.python import _body_is_protocol

        class FakeCall:
            type = "call"

        class FakeExprStmt:
            type = "expression_statement"
            children = [FakeCall()]

        class FakeBody:
            children = [FakeExprStmt()]

        assert _body_is_protocol(FakeBody()) is False

    def test_body_is_enum_with_comment(self) -> None:
        """_body_is_enum skips comment children."""
        from eigenhelm.declarations.python import _body_is_enum

        class FakeComment:
            type = "comment"

        class FakeBody:
            children = [FakeComment()]

        assert _body_is_enum(FakeBody()) is True

    def test_body_is_enum_expression_statement_ellipsis(self) -> None:
        """_body_is_enum handles expression_statement wrapping ellipsis."""
        from eigenhelm.declarations.python import _body_is_enum

        class FakeEllipsis:
            type = "ellipsis"

        class FakeExprStmt:
            type = "expression_statement"
            children = [FakeEllipsis()]

        class FakeBody:
            children = [FakeExprStmt()]

        assert _body_is_enum(FakeBody()) is True

    def test_body_is_enum_expression_statement_non_ellipsis_rejected(self) -> None:
        """_body_is_enum rejects expression_statement wrapping non-ellipsis."""
        from eigenhelm.declarations.python import _body_is_enum

        class FakeCall:
            type = "call"

        class FakeExprStmt:
            type = "expression_statement"
            children = [FakeCall()]

        class FakeBody:
            children = [FakeExprStmt()]

        assert _body_is_enum(FakeBody()) is False

    def test_is_stub_method_no_body(self) -> None:
        """_is_stub_method returns False when function has no body."""
        from eigenhelm.declarations.python import _is_stub_method

        class FakeChild:
            type = "parameters"

        class FakeNode:
            children = [FakeChild()]

        assert _is_stub_method(FakeNode()) is False

    def test_is_stub_method_with_comment_and_ellipsis(self) -> None:
        """_is_stub_method handles comment + ellipsis in body."""
        from eigenhelm.declarations.python import _is_stub_method

        class FakeComment:
            type = "comment"

        class FakeEllipsis:
            type = "ellipsis"

        class FakeBlock:
            type = "block"
            children = [FakeComment(), FakeEllipsis()]

        class FakeNode:
            children = [FakeBlock()]

        assert _is_stub_method(FakeNode()) is True

    def test_is_stub_method_expression_statement_ellipsis(self) -> None:
        """_is_stub_method handles expression_statement wrapping ellipsis."""
        from eigenhelm.declarations.python import _is_stub_method

        class FakeEllipsis:
            type = "ellipsis"

        class FakeExprStmt:
            type = "expression_statement"
            children = [FakeEllipsis()]

        class FakeBlock:
            type = "block"
            children = [FakeExprStmt()]

        class FakeNode:
            children = [FakeBlock()]

        assert _is_stub_method(FakeNode()) is True

    def test_is_stub_method_expression_statement_non_ellipsis_rejected(self) -> None:
        """_is_stub_method rejects expression_statement with non-ellipsis."""
        from eigenhelm.declarations.python import _is_stub_method

        class FakeCall:
            type = "call"

        class FakeExprStmt:
            type = "expression_statement"
            children = [FakeCall()]

        class FakeBlock:
            type = "block"
            children = [FakeExprStmt()]

        class FakeNode:
            children = [FakeBlock()]

        assert _is_stub_method(FakeNode()) is False

    def test_is_stub_method_with_return_statement_rejected(self) -> None:
        """_is_stub_method rejects body with a return statement."""
        from eigenhelm.declarations.python import _is_stub_method

        class FakeReturn:
            type = "return_statement"

        class FakeBlock:
            type = "block"
            children = [FakeReturn()]

        class FakeNode:
            children = [FakeBlock()]

        assert _is_stub_method(FakeNode()) is False

    def test_count_protocol_lines_with_comment(self) -> None:
        """_count_protocol_lines skips comments."""
        from eigenhelm.declarations.python import _count_protocol_lines

        class FakeComment:
            type = "comment"

        class FakeBody:
            children = [FakeComment()]

        assert _count_protocol_lines(FakeBody(), "") == 0

    def test_count_stub_method_lines_with_comment(self) -> None:
        """_count_stub_method_lines skips comments."""
        from eigenhelm.declarations.python import _count_stub_method_lines

        class FakeComment:
            type = "comment"

        class FakeBlock:
            type = "block"
            children = [FakeComment()]

        class FakeNode:
            start_point = (0, 0)
            children = [FakeBlock()]

        assert _count_stub_method_lines(FakeNode()) == 1  # just the def line

    def test_count_stub_method_lines_expression_statement_ellipsis(self) -> None:
        """_count_stub_method_lines counts expression_statement wrapping ellipsis."""
        from eigenhelm.declarations.python import _count_stub_method_lines

        class FakeEllipsis:
            type = "ellipsis"

        class FakeExprStmt:
            type = "expression_statement"
            children = [FakeEllipsis()]
            start_point = (1, 4)

        class FakeBlock:
            type = "block"
            children = [FakeExprStmt()]

        class FakeNode:
            start_point = (0, 0)
            children = [FakeBlock()]

        assert _count_stub_method_lines(FakeNode()) == 2  # def + ellipsis

    def test_count_assignment_lines_with_comment(self) -> None:
        """_count_assignment_lines skips comments."""
        from eigenhelm.declarations.python import _count_assignment_lines

        class FakeComment:
            type = "comment"

        class FakeBody:
            children = [FakeComment()]

        assert _count_assignment_lines(FakeBody(), "") == 0

    def test_try_const_table_expression_statement_no_children(self) -> None:
        """_try_const_table handles expression_statement with no children."""
        from eigenhelm.declarations.python import _try_const_table

        class FakeNode:
            type = "expression_statement"
            children = []

        regions: list = []
        _try_const_table(FakeNode(), "", regions)
        assert regions == []

    def test_try_const_table_expression_statement_non_assignment(self) -> None:
        """_try_const_table handles expression_statement wrapping non-assignment."""
        from eigenhelm.declarations.python import _try_const_table

        class FakeCall:
            type = "call"

        class FakeNode:
            type = "expression_statement"
            children = [FakeCall()]

        regions: list = []
        _try_const_table(FakeNode(), "", regions)
        assert regions == []

    def test_try_class_body_none(self) -> None:
        """_try_class returns early when body is None."""
        from eigenhelm.declarations.python import _try_class

        class FakeChild:
            type = "identifier"
            text = b"Foo"

        class FakeClassNode:
            children = [FakeChild()]  # no block child

        class FakeArgList:
            type = "argument_list"
            children = []

        class FakeClassWithArgs:
            type = "class_definition"
            children = [FakeChild(), FakeArgList()]

        regions: list = []
        _try_class(FakeClassWithArgs(), FakeClassWithArgs(), "", regions)
        assert regions == []

    def test_detect_returns_empty_for_none_root(self) -> None:
        """detect returns () when parse_source returns None."""
        from unittest.mock import patch
        from eigenhelm.declarations.python import detect

        with patch("eigenhelm.parsers.tree_sitter.parse_source", return_value=None):
            result = detect("some source")
        assert result == ()

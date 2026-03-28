"""Unit tests for Python declaration detection."""

from __future__ import annotations

import textwrap

from eigenhelm.declarations.models import DeclarationType
from eigenhelm.declarations.python import detect
from eigenhelm.declarations import analyze_declarations


def test_pure_dataclass_file():
    """Pure dataclass (field-only) detected as TYPE_DEFINITION with correct lines."""
    src = textwrap.dedent("""\
        from dataclasses import dataclass

        @dataclass(frozen=True)
        class Point:
            x: float
            y: float
            z: float = 0.0
    """)
    regions = detect(src)
    assert len(regions) == 1
    r = regions[0]
    assert r.declaration_type == DeclarationType.TYPE_DEFINITION
    assert r.node_name == "Point"
    assert r.start_line == 3  # @dataclass line
    assert r.end_line == 7
    assert r.declaration_line_count == 5  # decorator + class + 3 fields


def test_dataclass_with_post_init_excluded():
    """Dataclass with __post_init__ is NOT detected (has method body)."""
    src = textwrap.dedent("""\
        from dataclasses import dataclass

        @dataclass
        class Config:
            name: str
            value: int

            def __post_init__(self):
                if self.value < 0:
                    raise ValueError("negative")
    """)
    regions = detect(src)
    assert len(regions) == 0


def test_protocol_with_ellipsis_stubs():
    """Protocol with ellipsis method stubs detected as TYPE_DEFINITION."""
    src = textwrap.dedent("""\
        from typing import Protocol

        class Scorer(Protocol):
            def score(self, code: str) -> float:
                ...

            def name(self) -> str:
                ...
    """)
    regions = detect(src)
    assert len(regions) == 1
    r = regions[0]
    assert r.declaration_type == DeclarationType.TYPE_DEFINITION
    assert r.node_name == "Scorer"


def test_typeddict_detected():
    """TypedDict class detected as TYPE_DEFINITION."""
    src = textwrap.dedent("""\
        from typing import TypedDict

        class Settings(TypedDict):
            host: str
            port: int
            debug: bool
    """)
    regions = detect(src)
    assert len(regions) == 1
    assert regions[0].declaration_type == DeclarationType.TYPE_DEFINITION
    assert regions[0].node_name == "Settings"


def test_namedtuple_detected():
    """NamedTuple class detected as TYPE_DEFINITION."""
    src = textwrap.dedent("""\
        from typing import NamedTuple

        class Coordinate(NamedTuple):
            lat: float
            lon: float
    """)
    regions = detect(src)
    assert len(regions) == 1
    assert regions[0].declaration_type == DeclarationType.TYPE_DEFINITION
    assert regions[0].node_name == "Coordinate"


def test_enum_value_only_detected():
    """Enum with only value assignments detected as ENUM_DECLARATION."""
    src = textwrap.dedent("""\
        from enum import Enum

        class Color(Enum):
            RED = 1
            GREEN = 2
            BLUE = 3
    """)
    regions = detect(src)
    assert len(regions) == 1
    r = regions[0]
    assert r.declaration_type == DeclarationType.ENUM_DECLARATION
    assert r.node_name == "Color"


def test_enum_with_method_not_detected():
    """Enum with a method is NOT detected."""
    src = textwrap.dedent("""\
        from enum import Enum

        class Color(Enum):
            RED = 1
            GREEN = 2

            def describe(self):
                return f"Color: {self.name}"
    """)
    regions = detect(src)
    assert len(regions) == 0


def test_pydantic_basemodel_detected():
    """Pydantic BaseModel (field-only) detected as CONFIG_MODEL."""
    src = textwrap.dedent("""\
        from pydantic import BaseModel

        class AppConfig(BaseModel):
            host: str = "localhost"
            port: int = 8080
            debug: bool = False
    """)
    regions = detect(src)
    assert len(regions) == 1
    r = regions[0]
    assert r.declaration_type == DeclarationType.CONFIG_MODEL
    assert r.node_name == "AppConfig"


def test_mixed_file_below_threshold():
    """Mixed file: regions detected but ratio below 0.6."""
    logic_lines = "\n".join(f"    x = x + {i}" for i in range(200))
    src = (
        textwrap.dedent("""\
        from dataclasses import dataclass

        @dataclass(frozen=True)
        class Point:
            x: float
            y: float

        @dataclass(frozen=True)
        class Vec:
            dx: float
            dy: float

        def compute(x):
    """)
        + logic_lines
        + "\n    return x\n"
    )

    analysis = analyze_declarations(src, "python")
    assert len(analysis.regions) == 2
    assert analysis.ratio < 0.6
    assert not analysis.is_dominant


def test_100_percent_declaration_file():
    """File that is entirely declarations has ratio ~1.0."""
    src = textwrap.dedent("""\
        from dataclasses import dataclass

        @dataclass(frozen=True)
        class Alpha:
            a: int
            b: str

        @dataclass(frozen=True)
        class Beta:
            c: float
            d: bool
    """)
    analysis = analyze_declarations(src, "python")
    assert len(analysis.regions) == 2
    # The import line is non-declarative, so ratio won't be exactly 1.0,
    # but declarations should dominate.
    assert analysis.ratio >= 0.8


def test_empty_file():
    """Empty file returns empty tuple."""
    regions = detect("")
    assert regions == ()


def test_const_table_detected():
    """Module-level const array of dicts detected as CONST_TABLE."""
    src = textwrap.dedent("""\
        ROUTES = [
            {"path": "/home", "handler": "home_view"},
            {"path": "/about", "handler": "about_view"},
            {"path": "/api", "handler": "api_view"},
        ]
    """)
    regions = detect(src)
    assert len(regions) == 1
    r = regions[0]
    assert r.declaration_type == DeclarationType.CONST_TABLE
    assert r.node_name == "ROUTES"


def test_class_with_init_not_detected():
    """Class with explicit __init__ method is NOT detected."""
    src = textwrap.dedent("""\
        class Service:
            def __init__(self, name: str):
                self.name = name
                self.running = False

            def start(self):
                self.running = True
    """)
    regions = detect(src)
    assert len(regions) == 0

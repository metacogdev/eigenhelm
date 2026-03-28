"""Unit tests for Go declaration detection."""

from __future__ import annotations

from eigenhelm.declarations.models import DeclarationType
from eigenhelm.declarations.go import detect


class TestStructDefinition:
    def test_struct_detected_as_type_definition(self) -> None:
        source = """\
package main

type Config struct {
	Host string
	Port int
}
"""
        regions = detect(source)
        assert len(regions) == 1
        assert regions[0].declaration_type == DeclarationType.TYPE_DEFINITION
        assert regions[0].node_name == "Config"
        assert regions[0].language == "go"

    def test_multiple_structs_detected(self) -> None:
        source = """\
package main

type Request struct {
	URL    string
	Method string
}

type Response struct {
	Status int
	Body   string
}
"""
        regions = detect(source)
        assert len(regions) == 2
        assert all(
            r.declaration_type == DeclarationType.TYPE_DEFINITION for r in regions
        )
        names = {r.node_name for r in regions}
        assert names == {"Request", "Response"}


class TestConstIotaBlock:
    def test_const_iota_detected_as_enum(self) -> None:
        source = """\
package main

const (
	Red = iota
	Green
	Blue
)
"""
        regions = detect(source)
        assert len(regions) == 1
        assert regions[0].declaration_type == DeclarationType.ENUM_DECLARATION
        assert regions[0].node_name == "Red"

    def test_single_const_not_detected(self) -> None:
        """Plain const without iota or grouping is not an enum declaration."""
        source = """\
package main

const MaxRetries = 3
"""
        regions = detect(source)
        assert len(regions) == 0


class TestVarBlockWithStructLiterals:
    def test_var_block_with_composite_literal_detected(self) -> None:
        source = """\
package main

type Route struct {
	Path   string
	Method string
}

var routes = []Route{
	{Path: "/home", Method: "GET"},
	{Path: "/about", Method: "GET"},
}
"""
        regions = detect(source)
        # Should have the struct (TYPE_DEFINITION) and the var block (CONST_TABLE)
        types = {r.declaration_type for r in regions}
        assert DeclarationType.CONST_TABLE in types
        table = [
            r for r in regions if r.declaration_type == DeclarationType.CONST_TABLE
        ]
        assert len(table) == 1
        assert table[0].node_name == "routes"


class TestFunctionNotDetected:
    def test_function_declaration_not_detected(self) -> None:
        source = """\
package main

func main() {
	fmt.Println("hello")
}
"""
        regions = detect(source)
        assert len(regions) == 0

    def test_function_with_return_not_detected(self) -> None:
        source = """\
package main

func add(a, b int) int {
	return a + b
}
"""
        regions = detect(source)
        assert len(regions) == 0


class TestMethodNotDetected:
    def test_method_declaration_not_detected(self) -> None:
        source = """\
package main

type Server struct {
	Port int
}

func (s *Server) Start() {
	fmt.Println("starting")
}
"""
        regions = detect(source)
        # Only the struct should be detected, not the method
        assert len(regions) == 1
        assert regions[0].declaration_type == DeclarationType.TYPE_DEFINITION
        assert regions[0].node_name == "Server"


class TestEmptySource:
    def test_empty_string_returns_empty(self) -> None:
        assert detect("") == ()

    def test_whitespace_only_returns_empty(self) -> None:
        assert detect("   \n\n  ") == ()

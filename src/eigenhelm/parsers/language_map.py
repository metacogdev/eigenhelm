"""Language identifier → Tree-sitter grammar name and file extension mapping.

Adding a new language requires only adding an entry here — no code changes.
"""

from __future__ import annotations

# Maps canonical language identifier → (tree-sitter grammar name, file extension)
# Grammar name is what tree-sitter-languages.get_parser() / get_language() accepts.
LANGUAGE_MAP: dict[str, tuple[str, str]] = {
    "python": ("python", ".py"),
    "javascript": ("javascript", ".js"),
    "typescript": ("typescript", ".ts"),
    "go": ("go", ".go"),
    "rust": ("rust", ".rs"),
    "java": ("java", ".java"),
    "c": ("c", ".c"),
    "cpp": ("cpp", ".cpp"),
    "ruby": ("ruby", ".rb"),
    "kotlin": ("kotlin", ".kt"),
}

# Node types classified as OPERATORS for Halstead computation.
# These are AST-structural (language-agnostic): branch, control-flow,
# call, assignment, return nodes. Reference: Halstead (1977).
OPERATOR_NODE_TYPES: frozenset[str] = frozenset(
    {
        # Control flow
        "if_statement",
        "if",
        "elif_clause",
        "for_statement",
        "for",
        "for_in_statement",
        "while_statement",
        "while",
        "match_statement",
        "switch_statement",
        "case_clause",
        "case",
        # Branching / exception
        "try_statement",
        "catch_clause",
        "except_clause",
        "finally_clause",
        "with_statement",
        # Jump
        "return_statement",
        "return",
        "break_statement",
        "break",
        "continue_statement",
        "continue",
        "raise_statement",
        "throw_statement",
        # Calls
        "call",
        "call_expression",
        "method_invocation",
        # Assignment
        "assignment",
        "augmented_assignment",
        "variable_declarator",
        "short_var_declaration",
        # Logical / comparison operators (used as nodes in some grammars)
        "binary_operator",
        "unary_operator",
        "boolean_operator",
        "comparison_operator",
        # Definition keywords (structural)
        "function_definition",
        "function_declaration",
        "method_definition",
        "class_definition",
        "class_declaration",
    }
)


def get_grammar_name(language: str) -> str:
    """Return the tree-sitter grammar name for a language identifier.

    Raises:
        KeyError: if the language is not in LANGUAGE_MAP.
    """
    return LANGUAGE_MAP[language.lower()][0]


def get_extension(language: str) -> str:
    """Return the canonical file extension for a language (e.g., '.py').

    Raises:
        KeyError: if the language is not in LANGUAGE_MAP.
    """
    return LANGUAGE_MAP[language.lower()][1]


def is_supported(language: str) -> bool:
    """Return True if the language has a registered grammar mapping."""
    return language.lower() in LANGUAGE_MAP

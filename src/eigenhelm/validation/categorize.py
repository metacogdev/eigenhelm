"""File type categorization heuristics for benchmark stratification.

Classifies source files into categories (implementation, test, schema,
init, generated, unknown) using a layered heuristic:
  1. Override lookup (explicit per-file mapping)
  2. Filename pattern matching
  3. Directory location
  4. Content analysis
"""

from __future__ import annotations

import os
import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from eigenhelm.parsers.language_map import LANGUAGE_MAP
from eigenhelm.validation.usecase_models import FileCategory

# Extension → language mapping for file discovery
_EXT_TO_LANG: dict[str, str] = {ext: lang for lang, (_, ext) in LANGUAGE_MAP.items()}

# Config/data file extensions that are always "schema"
_CONFIG_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".toml",
        ".yaml",
        ".yml",
        ".json",
        ".cfg",
        ".ini",
    }
)

# Directory names that indicate test files
_TEST_DIRS: frozenset[str] = frozenset({"tests", "test", "testing"})

# Directory names that indicate schema/type definition files
_SCHEMA_DIRS: frozenset[str] = frozenset({"models", "schemas", "types"})

# Directory names that indicate generated files
_GENERATED_DIRS: frozenset[str] = frozenset({"generated", "proto", "_generated", "gen"})

# Regex for generated file markers (checked in first 10 lines)
_GENERATED_MARKERS = re.compile(r"^\s*#\s*(?:Generated\s+by|@generated)", re.IGNORECASE)

_SKIP_DIRS: frozenset[str] = frozenset(
    {
        ".git",
        "__pycache__",
        ".venv",
        "venv",
        "node_modules",
        ".pytest_cache",
        "dist",
        "build",
    }
)

_SUPPORTED_EXTENSIONS: frozenset[str] = (
    frozenset(_EXT_TO_LANG.keys()) | {".py"} | _CONFIG_EXTENSIONS
)


@dataclass(frozen=True)
class _CategorizationContext:
    path: Path
    path_str: str
    name: str
    parts: frozenset[str]
    content: str | None
    overrides: dict[str, FileCategory] | None


_CategoryRule = Callable[[_CategorizationContext], FileCategory | None]


def categorize_file(
    file_path: str | Path,
    content: str | None = None,
    overrides: dict[str, FileCategory] | None = None,
) -> FileCategory:
    """Categorize a source file by type using layered heuristics.

    Args:
        file_path: Path to the file (relative or absolute).
        content: File content (if already loaded). Avoids re-reading.
        overrides: Optional mapping of path strings to forced categories.

    Returns:
        FileCategory classification.
    """
    path = Path(file_path)
    context = _CategorizationContext(
        path=path,
        path_str=str(path),
        name=path.name,
        parts=frozenset(path.parts),
        content=content,
        overrides=overrides,
    )
    for rule in _CATEGORY_RULES:
        category = rule(context)
        if category is not None:
            return category
    return FileCategory.UNKNOWN


def _override_rule(context: _CategorizationContext) -> FileCategory | None:
    if context.overrides and context.path_str in context.overrides:
        return context.overrides[context.path_str]
    return None


def _config_extension_rule(context: _CategorizationContext) -> FileCategory | None:
    if context.path.suffix in _CONFIG_EXTENSIONS:
        return FileCategory.SCHEMA
    return None


def _filename_rule(context: _CategorizationContext) -> FileCategory | None:
    if context.name.startswith("test_") or context.name.endswith("_test.py"):
        return FileCategory.TEST
    if context.name == "__init__.py":
        return _categorize_init(context.content)
    return None


def _directory_rule(context: _CategorizationContext) -> FileCategory | None:
    if context.parts & _TEST_DIRS:
        return FileCategory.TEST
    if context.parts & _GENERATED_DIRS:
        return FileCategory.GENERATED
    return None


def _content_rule(context: _CategorizationContext) -> FileCategory | None:
    if context.content is None:
        return _missing_content_schema_rule(context)
    if _has_generated_marker(context.content):
        return FileCategory.GENERATED
    if context.parts & _SCHEMA_DIRS and _is_schema_content(context.content):
        return FileCategory.SCHEMA
    return None


def _missing_content_schema_rule(
    context: _CategorizationContext,
) -> FileCategory | None:
    if context.parts & _SCHEMA_DIRS:
        return FileCategory.SCHEMA
    return None


def _source_extension_rule(context: _CategorizationContext) -> FileCategory | None:
    if context.path.suffix in _EXT_TO_LANG or context.path.suffix == ".py":
        return FileCategory.IMPLEMENTATION
    return None


_CATEGORY_RULES: tuple[_CategoryRule, ...] = (
    _override_rule,
    _config_extension_rule,
    _filename_rule,
    _directory_rule,
    _content_rule,
    _source_extension_rule,
)


def _categorize_init(content: str | None) -> FileCategory:
    """Classify an __init__.py as INIT (re-export) or IMPLEMENTATION."""
    if content is None:
        return FileCategory.INIT  # assume re-export without content

    lines = _meaningful_lines(content)
    if not lines:
        return FileCategory.INIT

    # Short files that are mostly imports → INIT
    if len(lines) < 50 and _mostly_init_imports(lines):
        return FileCategory.INIT

    return FileCategory.IMPLEMENTATION


def _meaningful_lines(content: str) -> list[str]:
    return [
        ln.strip()
        for ln in content.splitlines()
        if ln.strip() and not ln.strip().startswith("#")
    ]


def _mostly_init_imports(lines: list[str]) -> bool:
    import_lines = sum(
        1
        for ln in lines
        if ln.startswith(("import ", "from ")) or ln.startswith("__all__")
    )
    return import_lines / len(lines) > 0.5


def _is_schema_content(content: str) -> bool:
    """Check if content looks like schema/type definitions rather than logic.

    Schema files typically have classes/type aliases but few standalone
    function definitions with logic.
    """
    lines = _meaningful_lines(content)
    if not lines:
        return True  # empty file in schema dir → schema

    class_lines, type_lines, def_lines = _schema_indicators(lines)
    return _has_schema_shape(class_lines, type_lines, def_lines) or _short_without_defs(
        lines, def_lines
    )


def _schema_indicators(lines: list[str]) -> tuple[int, int, int]:
    class_lines = sum(1 for ln in lines if ln.startswith("class "))
    type_lines = sum(1 for ln in lines if ln.startswith("type "))
    def_lines = sum(1 for ln in lines if _is_standalone_def(ln))
    return class_lines, type_lines, def_lines


def _is_standalone_def(line: str) -> bool:
    return line.startswith("def ") and not line.startswith("def __")


def _has_schema_shape(class_lines: int, type_lines: int, def_lines: int) -> bool:
    structural_lines = class_lines + type_lines
    return structural_lines > 0 and def_lines <= structural_lines


def _short_without_defs(lines: list[str], def_lines: int) -> bool:
    return len(lines) < 20 and def_lines == 0


def _has_generated_marker(content: str) -> bool:
    first_lines = "\n".join(content.split("\n")[:10])
    return _GENERATED_MARKERS.search(first_lines) is not None


def categorize_directory(
    dir_path: Path,
    overrides: dict[str, FileCategory] | None = None,
) -> dict[Path, FileCategory]:
    """Walk a directory and categorize all supported source files.

    Args:
        dir_path: Root directory to scan.
        overrides: Optional per-file category overrides.

    Returns:
        Mapping of file paths to their categories.
    """
    results: dict[Path, FileCategory] = {}
    for root, dirs, files in os.walk(dir_path, followlinks=False):
        _prune_non_source_dirs(dirs)

        for filename in files:
            child = Path(root) / filename
            if not _is_categorizable_file(child):
                continue
            content = _read_text(child)
            if content is None:
                continue

            rel_path = child.relative_to(dir_path)
            category = categorize_file(
                str(rel_path), content=content, overrides=overrides
            )
            results[rel_path] = category

    return results


def _prune_non_source_dirs(dirs: list[str]) -> None:
    dirs[:] = [d for d in dirs if d not in _SKIP_DIRS and not d.endswith(".egg-info")]


def _is_categorizable_file(child: Path) -> bool:
    return child.suffix in _SUPPORTED_EXTENSIONS and not child.is_symlink()


def _read_text(child: Path) -> str | None:
    try:
        return child.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None

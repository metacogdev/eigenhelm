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
    path_str = str(path)

    # 1. Override lookup
    if overrides and path_str in overrides:
        return overrides[path_str]

    # 2. Config file extensions (not source code)
    if path.suffix in _CONFIG_EXTENSIONS:
        return FileCategory.SCHEMA

    # 3. Filename patterns
    name = path.name

    # Test files by name
    if name.startswith("test_") or name.endswith("_test.py"):
        return FileCategory.TEST

    # Init files — need content analysis to distinguish re-export from logic
    if name == "__init__.py":
        return _categorize_init(content)

    # 4. Directory location
    parts = set(path.parts)

    if parts & _TEST_DIRS:
        return FileCategory.TEST

    if parts & _GENERATED_DIRS:
        return FileCategory.GENERATED

    # 5. Content analysis (needs content)
    if content is not None:
        # Generated file markers
        first_lines = "\n".join(content.split("\n")[:10])
        if _GENERATED_MARKERS.search(first_lines):
            return FileCategory.GENERATED

        # Schema directory + schema-like content (class-heavy or no standalone functions)
        if parts & _SCHEMA_DIRS and _is_schema_content(content):
            return FileCategory.SCHEMA

    elif parts & _SCHEMA_DIRS:
        # No content available but in a schema directory — assume schema
        return FileCategory.SCHEMA

    # 6. Default: implementation
    if path.suffix in _EXT_TO_LANG or path.suffix == ".py":
        return FileCategory.IMPLEMENTATION

    return FileCategory.UNKNOWN


def _categorize_init(content: str | None) -> FileCategory:
    """Classify an __init__.py as INIT (re-export) or IMPLEMENTATION."""
    if content is None:
        return FileCategory.INIT  # assume re-export without content

    lines = [
        ln.strip()
        for ln in content.splitlines()
        if ln.strip() and not ln.strip().startswith("#")
    ]
    if not lines:
        return FileCategory.INIT

    # Short files that are mostly imports → INIT
    if len(lines) < 50:
        import_lines = sum(
            1
            for ln in lines
            if ln.startswith(("import ", "from ")) or ln.startswith("__all__")
        )
        if import_lines / len(lines) > 0.5:
            return FileCategory.INIT

    return FileCategory.IMPLEMENTATION


def _is_schema_content(content: str) -> bool:
    """Check if content looks like schema/type definitions rather than logic.

    Schema files typically have classes/type aliases but few standalone
    function definitions with logic.
    """
    lines = [
        ln
        for ln in content.splitlines()
        if ln.strip() and not ln.strip().startswith("#")
    ]
    if not lines:
        return True  # empty file in schema dir → schema

    # Count structural indicators
    class_lines = sum(1 for ln in lines if ln.strip().startswith("class "))
    type_lines = sum(1 for ln in lines if ln.strip().startswith("type "))
    def_lines = sum(
        1
        for ln in lines
        if ln.strip().startswith("def ") and not ln.strip().startswith("def __")
    )

    # Has classes or type aliases, and few standalone function defs → schema
    if (class_lines + type_lines) > 0 and def_lines <= (class_lines + type_lines):
        return True

    # Short file with no function defs → likely config/schema
    if len(lines) < 20 and def_lines == 0:
        return True

    return False


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
    supported_exts = set(_EXT_TO_LANG.keys()) | {".py"} | _CONFIG_EXTENSIONS

    for root, dirs, files in os.walk(dir_path, followlinks=False):
        # Prune common non-source directories
        dirs[:] = [
            d
            for d in dirs
            if d
            not in {
                ".git",
                "__pycache__",
                ".venv",
                "venv",
                "node_modules",
                ".pytest_cache",
                "dist",
                "build",
            }
            and not d.endswith(".egg-info")
        ]

        for filename in files:
            child = Path(root) / filename
            if child.suffix not in supported_exts:
                continue
            if child.is_symlink():
                continue

            try:
                content = child.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue

            rel_path = child.relative_to(dir_path)
            category = categorize_file(
                str(rel_path), content=content, overrides=overrides
            )
            results[rel_path] = category

    return results

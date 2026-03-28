"""Barrel/module-shipping file detection.

Detects files that are primarily import/export re-exports with no
meaningful logic. These files produce noisy scores and are skipped
from evaluation.
"""

from __future__ import annotations

# Threshold: if >= 80% of non-blank lines are imports/exports,
# the file is a barrel file.
_BARREL_THRESHOLD = 0.80


def is_barrel_file(source: str, language: str) -> bool:
    """Return True if the file is primarily imports/exports.

    Args:
        source: Source code string.
        language: Language identifier.

    Returns:
        True if the file is a module-shipping barrel file.
    """
    if not source.strip():
        return False

    lines = source.splitlines()
    non_blank = [line for line in lines if line.strip()]
    if len(non_blank) < 2:
        return False

    detector = _DETECTORS.get(language)
    if detector is None:
        return False

    import_lines = sum(1 for line in non_blank if detector(line.strip()))
    ratio = import_lines / len(non_blank)
    return ratio >= _BARREL_THRESHOLD


def _is_python_import(line: str) -> bool:
    """Check if a line is a Python import, __all__, or continuation thereof."""
    if line.startswith(("import ", "from ")):
        return True
    if line.startswith("__all__"):
        return True
    # Closing parens/brackets for multi-line imports or __all__
    if line in (")", "]", "},", ");", "],"):
        return True
    # Quoted strings in __all__ = [...] lists
    if line.startswith(('"', "'")):
        return True
    # Indented import continuation lines (imported names)
    stripped = line.lstrip()
    if stripped and not stripped.startswith(
        (
            "def ",
            "class ",
            "if ",
            "for ",
            "while ",
            "return ",
            "raise ",
            "try ",
            "with ",
            "async ",
        )
    ):
        # Could be a continuation of a multi-line import or __all__
        # Only count if it looks like a name or string, not logic
        if (
            stripped.rstrip(",")
            .rstrip(")")
            .rstrip("]")
            .replace('"', "")
            .replace("'", "")
            .replace(" ", "")
            .isidentifier()
        ):
            return True
    # Comment lines
    if line.startswith("#"):
        return True
    return False


def _is_js_ts_import(line: str) -> bool:
    """Check if a line is a JS/TS import or export statement."""
    if line.startswith(("import ", "export ")):
        return True
    # Re-export: export { X } from or export * from
    if line.startswith(("} from", "};", "}")):
        return True
    # Continuation of multi-line imports
    if line.startswith((" ", "\t")) and not line.lstrip().startswith(
        (
            "function ",
            "class ",
            "const ",
            "let ",
            "var ",
            "if ",
            "for ",
            "while ",
            "return ",
        )
    ):
        return True
    if line.startswith("//"):
        return True
    return False


def _is_rust_use(line: str) -> bool:
    """Check if a line is a Rust use/mod declaration."""
    if line.startswith(("use ", "pub use ", "mod ", "pub mod ")):
        return True
    # Continuation of multi-line use statements
    if line.startswith(("}", "};", "},")):
        return True
    if line.startswith((" ", "\t")) and not line.lstrip().startswith(
        (
            "fn ",
            "pub fn ",
            "struct ",
            "enum ",
            "impl ",
            "trait ",
            "const ",
            "static ",
            "type ",
            "let ",
            "if ",
            "for ",
            "while ",
            "return ",
            "match ",
        )
    ):
        return True
    if line.startswith("//"):
        return True
    return False


_DETECTORS = {
    "python": _is_python_import,
    "javascript": _is_js_ts_import,
    "typescript": _is_js_ts_import,
    "rust": _is_rust_use,
}

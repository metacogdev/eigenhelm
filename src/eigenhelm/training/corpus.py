"""Corpus walking, language detection, and SHA-256 hashing."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

from eigenhelm.parsers.language_map import LANGUAGE_MAP

# Reverse map: file extension → canonical language key (single source of truth).
# Derived from LANGUAGE_MAP so adding a new language automatically supports it here.
EXTENSION_TO_LANGUAGE: dict[str, str] = {
    ext: lang for lang, (_grammar, ext) in LANGUAGE_MAP.items()
}

DEFAULT_EXCLUDES = {
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    "node_modules",
    ".pytest_cache",
    "dist",
    "build",
}


def discover_corpus_files(corpus_dir: Path) -> list[Path]:
    """Return eligible source files under corpus_dir sorted by relative POSIX path.

    Walks corpus_dir recursively using os.walk to allow pruning ignored directories.
    Filters by EXTENSION_TO_LANGUAGE, and returns absolute Path objects sorted by
    their relative POSIX path string.
    """
    eligible = []

    # Optional .eigenhelmignore support
    excludes = set(DEFAULT_EXCLUDES)
    ignore_file = corpus_dir / ".eigenhelmignore"
    if ignore_file.is_file():
        try:
            custom_excludes = [
                line.strip()
                for line in ignore_file.read_text().splitlines()
                if line.strip() and not line.startswith("#")
            ]
            excludes.update(custom_excludes)
        except OSError:
            pass

    for root, dirs, files in os.walk(corpus_dir, followlinks=False):
        # Prune excluded directories in-place (also ignore .egg-info)
        retained = [
            d for d in dirs if d not in excludes and not d.endswith(".egg-info")
        ]
        dirs.clear()
        dirs.extend(retained)

        for filename in files:
            if filename in excludes:
                continue

            child = Path(root) / filename
            try:
                if child.is_symlink() or not child.is_file():
                    continue
                if child.suffix in EXTENSION_TO_LANGUAGE:
                    eligible.append(child)
            except OSError:
                # Catch PermissionError or other filesystem bounds
                continue

    return sorted(eligible, key=lambda p: p.relative_to(corpus_dir).as_posix())


def compute_corpus_hash(files: list[Path]) -> str:
    """Return a 64-character SHA-256 hex digest of the corpus.

    Iterates files (must be pre-sorted by caller), reads each file's bytes,
    and feeds them into a single SHA-256 stream. Paths are NOT hashed —
    only byte contents. No separators or delimiters between files.
    """
    h = hashlib.sha256()
    for f in files:
        h.update(f.read_bytes())
    return h.hexdigest()

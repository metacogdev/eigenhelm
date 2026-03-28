"""Git diff file discovery for eigenhelm diff-aware evaluation.

Provides discover_changed_files() which uses `git diff --name-only` to find
files changed in a given revision range.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from eigenhelm.parsers.language_map import LANGUAGE_MAP

# Set of recognized file extensions
_RECOGNIZED_EXTENSIONS: frozenset[str] = frozenset(
    ext for _, (_, ext) in LANGUAGE_MAP.items()
)


def discover_changed_files(revision_range: str) -> list[Path]:
    """Discover files changed in a git revision range.

    Runs `git diff --name-only --diff-filter=ACMR <revision_range>` to find
    added, copied, modified, or renamed files. Deleted files are excluded.

    Args:
        revision_range: A git revision range string (e.g., "HEAD~1", "main..feature").

    Returns:
        List of Path objects for changed files with recognized extensions,
        relative to the current working directory.

    Raises:
        RuntimeError: If git is not available or the revision range is invalid.
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=ACMR", revision_range],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("git not found. Is git installed and on PATH?") from exc

    if result.returncode != 0:
        stderr = result.stderr.strip()
        raise RuntimeError(
            f"git diff failed for revision range {revision_range!r}: {stderr}"
        )

    changed: list[Path] = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        p = Path(line)
        if p.suffix in _RECOGNIZED_EXTENSIONS:
            changed.append(p)

    return changed

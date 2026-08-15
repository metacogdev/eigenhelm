"""Content-hash cache for eigenhelm-check pre-commit evaluations.

Cache file: .eigenhelm/cache.json
Format:
  {
    "version": 1,
    "config_hash": "<SHA-256 of .eigenhelm.toml contents>",
    "entries": {
      "path/to/file.py": {
        "content_hash": "<SHA-256>",
        "decision": "accept",
        "score": 0.2
      }
    }
  }
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

_CACHE_VERSION = 1
_CACHE_FILE = Path(".eigenhelm") / "cache.json"


@dataclass
class CacheEntry:
    content_hash: str
    decision: str
    score: float


class EvaluationCache:
    """Content-hash cache for pre-commit evaluations.

    Invalidated when .eigenhelm.toml changes (via config_hash).
    """

    def __init__(self, cache_path: Path, config_hash: str) -> None:
        self._path = cache_path
        self._config_hash = config_hash
        self._entries: dict[str, CacheEntry] = {}
        self._load()

    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            if data.get("version") != _CACHE_VERSION:
                return  # Incompatible version
            if data.get("config_hash") != self._config_hash:
                return  # Config changed — invalidate
            for path_str, entry_data in data.get("entries", {}).items():
                self._entries[path_str] = CacheEntry(**entry_data)
        except (json.JSONDecodeError, KeyError, TypeError):
            pass  # Corrupt cache — start fresh

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": _CACHE_VERSION,
            "config_hash": self._config_hash,
            "entries": {k: asdict(v) for k, v in self._entries.items()},
        }
        self._path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def get(self, path: str, content_hash: str) -> CacheEntry | None:
        """Return cached entry if the content hash matches, else None."""
        entry = self._entries.get(path)
        if entry is not None and entry.content_hash == content_hash:
            return entry
        return None

    def set(self, path: str, entry: CacheEntry) -> None:
        self._entries[path] = entry

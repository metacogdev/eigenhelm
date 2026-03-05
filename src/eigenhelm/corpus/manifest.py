"""Corpus manifest schema: CorpusTarget and CorpusManifest frozen dataclasses."""

from __future__ import annotations

import hashlib
import json
import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CorpusTarget:
    """One repository contributing to the training corpus."""

    name: str
    url: str
    ref: str
    include: tuple[str, ...]
    exclude: tuple[str, ...]
    description: str

    def __post_init__(self) -> None:
        n = self.name or "<unnamed>"
        if not self.name:
            raise ValueError("target: 'name' must be non-empty")
        if not self.url:
            raise ValueError(f"target '{n}': 'url' must be non-empty")
        if not self.url.startswith("https://"):
            raise ValueError(f"target '{n}': 'url' must start with 'https://'")
        if not self.ref:
            raise ValueError(f"target '{n}': 'ref' must be non-empty")
        if not self.description:
            raise ValueError(f"target '{n}': 'description' must be non-empty")
        self._validate_patterns()

    def _validate_patterns(self) -> None:
        n = self.name
        if not self.include:
            raise ValueError(f"target '{n}': 'include' must have at least one pattern")
        for pat in self.include:
            if not pat:
                raise ValueError(f"target '{n}': 'include' contains an empty pattern")
        for pat in self.exclude:
            if not pat:
                raise ValueError(f"target '{n}': 'exclude' contains an empty pattern")

    @property
    def archive_url(self) -> str:
        """GitHub archive URL.

        Tag refs: ``{url}/archive/refs/tags/{ref}.tar.gz``
        SHA refs (40-char hex): ``{url}/archive/{ref}.tar.gz``
        """
        ref_lower = self.ref.lower()
        if len(self.ref) == 40 and all(c in "0123456789abcdef" for c in ref_lower):
            return f"{self.url}/archive/{self.ref}.tar.gz"
        return f"{self.url}/archive/refs/tags/{self.ref}.tar.gz"

    def entry_hash(self) -> str:
        """SHA-256 of canonicalized ``{name, url, ref, include, exclude}``.

        Used as the idempotency key in the sync sentinel. Changes whenever
        any field that affects extraction changes.
        """
        canonical = json.dumps(
            {
                "name": self.name,
                "url": self.url,
                "ref": self.ref,
                "include": list(self.include),
                "exclude": list(self.exclude),
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return "sha256:" + hashlib.sha256(canonical.encode()).hexdigest()

    @classmethod
    def from_dict(cls, d: dict, idx: int) -> CorpusTarget:
        """Parse a target dict from TOML.

        Uses ``idx`` in error messages when ``name`` is absent.
        """
        label = repr(d["name"]) if "name" in d else f"<target {idx}>"
        for field in ("name", "url", "ref", "description"):
            if field not in d:
                raise ValueError(f"target {label}: missing required field '{field}'")
        if "include" not in d:
            raise ValueError(f"target {label}: missing required field 'include'")
        return cls(
            name=d["name"],
            url=d["url"],
            ref=d["ref"],
            include=tuple(d["include"]),
            exclude=tuple(d.get("exclude", [])),
            description=d["description"],
        )


@dataclass(frozen=True)
class CorpusManifest:
    """Complete, versioned corpus declaration."""

    name: str
    version: str
    corpus_class: str
    created: str
    targets: tuple[CorpusTarget, ...]
    language: str | None = None

    def __post_init__(self) -> None:
        for fname in ("name", "version", "corpus_class", "created"):
            if not getattr(self, fname):
                raise ValueError(f"corpus.{fname} must be non-empty")
        if self.corpus_class not in {"A", "B", "C"}:
            raise ValueError(f"corpus.class must be 'A', 'B', or 'C'; got '{self.corpus_class}'")
        if self.corpus_class == "A" and not self.language:
            raise ValueError("corpus.language is required when corpus.class == 'A'")
        if not self.targets:
            raise ValueError("manifest must have at least one [[target]]")
        seen: set[str] = set()
        for t in self.targets:
            if t.name in seen:
                raise ValueError(f"duplicate target name: '{t.name}'")
            seen.add(t.name)

    @classmethod
    def from_dict(cls, d: dict) -> CorpusManifest:
        """Parse a TOML-decoded dict into a validated CorpusManifest."""
        corpus = d.get("corpus", {})
        for fname in ("name", "version", "created"):
            if fname not in corpus:
                raise ValueError(f"corpus.{fname} is required")
        if "class" not in corpus:
            raise ValueError("corpus.class is required")
        targets = tuple(CorpusTarget.from_dict(t, idx) for idx, t in enumerate(d.get("target", [])))
        return cls(
            name=corpus["name"],
            version=corpus["version"],
            corpus_class=corpus["class"],
            created=corpus["created"],
            language=corpus.get("language"),
            targets=targets,
        )


def load_manifest(path: str | Path) -> CorpusManifest:
    """Parse and validate a TOML corpus manifest file.

    Args:
        path: Path to the ``.toml`` manifest file.

    Returns:
        A fully validated, immutable :class:`CorpusManifest`.

    Raises:
        FileNotFoundError: If ``path`` does not exist.
        ValueError: If any required field is missing or invalid.
        tomllib.TOMLDecodeError: If the file is not valid TOML.
    """
    path = Path(path)
    with open(path, "rb") as fh:
        data = tomllib.load(fh)
    return CorpusManifest.from_dict(data)

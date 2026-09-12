"""Model registry — discover, download, and manage eigenhelm models.

Public API:
    fetch_manifest() — download and parse the remote registry manifest
    list_remote() — list available models from the registry
    list_local() — list locally available models (bundled + downloaded)
    pull_model() — download a model to the local cache
    resolve_model() — find a model by name (local first, then remote)
"""

from __future__ import annotations

import hashlib
import json
import shutil
import os
import urllib.request
from eigenhelm.config import find_config, load_config
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

from eigenhelm.registry.models import LocalModel, ModelEntry

__all__ = [
    "LocalModel",
    "ModelEntry",
    "RegistryError",
    "fetch_manifest",
    "list_local",
    "list_remote",
    "pull_model",
    "resolve_model",
]

# Default registry URL — points to a JSON manifest hosted on GitHub
_DEFAULT_REGISTRY_URL = (
    "https://raw.githubusercontent.com/metacogdev/eigenhelm-models/main/registry.json"
)

# Local cache directory for downloaded models
_DEFAULT_CACHE_DIR = Path.home() / ".eigenhelm" / "models"

_MANIFEST_TIMEOUT_S = 15  # Short timeout for JSON manifest fetches to fail fast
_DOWNLOAD_TIMEOUT_S = 60  # Longer timeout for multi-megabyte model downloads


def _get_registry_url() -> str:
    url = os.getenv("EIGENHELM_REGISTRY_URL")
    if url:
        return url
    cfg_path = find_config(Path.cwd())
    if cfg_path:
        try:
            cfg = load_config(cfg_path)
            if cfg.registry.url:
                return cfg.registry.url
        except Exception:
            pass
    return _DEFAULT_REGISTRY_URL


def _get_cache_dir() -> Path:
    d = os.getenv("EIGENHELM_CACHE_DIR")
    if d:
        return Path(d)
    cfg_path = find_config(Path.cwd())
    if cfg_path:
        try:
            cfg = load_config(cfg_path)
            if cfg.registry.cache_dir:
                return Path(cfg.registry.cache_dir)
        except Exception:
            pass
    return _DEFAULT_CACHE_DIR


class RegistryError(Exception):
    """Raised when a registry operation fails."""


def fetch_manifest(
    registry_url: str | None = None,
) -> tuple[ModelEntry, ...]:
    """Fetch and parse the remote registry manifest.

    Returns:
        Tuple of ModelEntry from the registry.

    Raises:
        RegistryError: If the manifest cannot be fetched or parsed.
    """
    try:
        registry_url = registry_url or _get_registry_url()
        with urllib.request.urlopen(registry_url, timeout=_MANIFEST_TIMEOUT_S) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        raise RegistryError(f"Failed to fetch registry: {exc}") from exc

    entries = []
    for item in data.get("models", []):
        try:
            entries.append(ModelEntry(**item))
        except TypeError as exc:
            raise RegistryError(f"Invalid model entry: {exc}") from exc

    return tuple(entries)


def list_remote(
    registry_url: str | None = None,
) -> tuple[ModelEntry, ...]:
    """List available models from the remote registry."""
    return fetch_manifest(registry_url)


def list_local() -> tuple[LocalModel, ...]:
    """List locally available models (bundled + downloaded).

    Bundled models come from the eigenhelm package.
    Downloaded models live in ~/.eigenhelm/models/.
    """
    models: list[LocalModel] = []

    # Bundled models
    try:
        from importlib import resources

        bundled_dir = resources.files("eigenhelm.trained_models")
        for item in bundled_dir.iterdir():
            name = item.name
            if name.endswith(".npz"):
                models.append(
                    LocalModel(
                        name=name.removesuffix(".npz"),
                        path=str(item),
                        bundled=True,
                    )
                )
    except Exception:
        pass

    # Downloaded models
    if _get_cache_dir().exists():
        for f in sorted(_get_cache_dir().glob("*.npz")):
            name = f.stem
            # Don't duplicate if also bundled
            if not any(m.name == name for m in models):
                models.append(LocalModel(name=name, path=str(f), bundled=False))

    return tuple(sorted(models, key=lambda m: m.name))


def pull_model(
    name: str,
    registry_url: str | None = None,
    force: bool = False,
) -> Path:
    """Download a model from the registry to the local cache.

    Args:
        name: Model name (without .npz extension).
        registry_url: Registry manifest URL.
        force: Re-download even if already cached.

    Returns:
        Path to the downloaded .npz file.

    Raises:
        RegistryError: If the model is not found or download fails.
    """
    manifest = fetch_manifest(registry_url)
    entry = _find_entry(name, manifest)
    if entry is None:
        available = ", ".join(e.name for e in manifest)
        raise RegistryError(
            f"Model '{name}' not found in registry. Available: {available}"
        )

    dest = _get_cache_dir() / f"{entry.name}.npz"
    if dest.exists() and not force:
        # Verify integrity
        if _sha256_file(dest) == entry.sha256:
            return dest
        # Hash mismatch — re-download

    _get_cache_dir().mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".npz.tmp")

    try:
        with urllib.request.urlopen(
            entry.download_url, timeout=_DOWNLOAD_TIMEOUT_S
        ) as resp:
            with open(tmp, "wb") as f:
                shutil.copyfileobj(resp, f)
    except Exception as exc:
        tmp.unlink(missing_ok=True)
        raise RegistryError(f"Download failed: {exc}") from exc

    # Verify SHA256
    actual = _sha256_file(tmp)
    if actual != entry.sha256:
        tmp.unlink(missing_ok=True)
        raise RegistryError(
            f"SHA256 mismatch for '{name}': "
            f"expected {entry.sha256[:16]}..., got {actual[:16]}..."
        )

    tmp.rename(dest)
    return dest


def resolve_model(name: str) -> Path | None:
    """Find a model by name — checks local cache and bundled models.

    Does NOT download from the registry. Returns None if not found locally.
    """
    # Check bundled
    for m in list_local():
        if m.name == name:
            return Path(m.path)
    return None


def _find_entry(name: str, manifest: tuple[ModelEntry, ...]) -> ModelEntry | None:
    for entry in manifest:
        if entry.name == name:
            return entry
    return None


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

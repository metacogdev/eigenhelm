"""Unit tests for the model registry module (eigenhelm.registry).

Covers: fetch_manifest, list_remote, list_local, pull_model, resolve_model,
_find_entry, _sha256_file, and RegistryError.
All HTTP calls are mocked — no network access.
"""

from __future__ import annotations

import hashlib
import json
from unittest.mock import MagicMock, patch

import pytest

from eigenhelm.registry import (
    RegistryError,
    _find_entry,
    _sha256_file,
    fetch_manifest,
    list_local,
    list_remote,
    pull_model,
    resolve_model,
)
from eigenhelm.registry.models import ModelEntry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_entry(**overrides) -> dict:
    defaults = {
        "name": "test-model",
        "description": "A test model",
        "language": "python",
        "corpus_class": "A",
        "n_components": 10,
        "n_training_files": 100,
        "download_url": "https://example.com/test-model.npz",
        "sha256": "abc123" * 10 + "abcd",
        "size_bytes": 1024,
        "version": "1.0.0",
    }
    defaults.update(overrides)
    return defaults


def _manifest_json(models: list[dict]) -> bytes:
    return json.dumps({"models": models}).encode("utf-8")


# ---------------------------------------------------------------------------
# fetch_manifest
# ---------------------------------------------------------------------------


class TestFetchManifest:
    def test_success(self):
        entry = _make_entry()
        body = _manifest_json([entry])
        resp = MagicMock()
        resp.read.return_value = body
        resp.__enter__ = lambda s: s
        resp.__exit__ = MagicMock(return_value=False)

        with patch("eigenhelm.registry.urllib.request.urlopen", return_value=resp):
            result = fetch_manifest("https://example.com/registry.json")

        assert len(result) == 1
        assert isinstance(result[0], ModelEntry)
        assert result[0].name == "test-model"

    def test_network_error_raises_registry_error(self):
        with patch(
            "eigenhelm.registry.urllib.request.urlopen",
            side_effect=ConnectionError("no network"),
        ):
            with pytest.raises(RegistryError, match="Failed to fetch registry"):
                fetch_manifest("https://example.com/registry.json")

    def test_invalid_model_entry_raises_registry_error(self):
        """Missing required fields in model entry."""
        body = json.dumps({"models": [{"name": "bad"}]}).encode("utf-8")
        resp = MagicMock()
        resp.read.return_value = body
        resp.__enter__ = lambda s: s
        resp.__exit__ = MagicMock(return_value=False)

        with patch("eigenhelm.registry.urllib.request.urlopen", return_value=resp):
            with pytest.raises(RegistryError, match="Invalid model entry"):
                fetch_manifest("https://example.com/registry.json")

    def test_empty_models_list(self):
        body = json.dumps({"models": []}).encode("utf-8")
        resp = MagicMock()
        resp.read.return_value = body
        resp.__enter__ = lambda s: s
        resp.__exit__ = MagicMock(return_value=False)

        with patch("eigenhelm.registry.urllib.request.urlopen", return_value=resp):
            result = fetch_manifest("https://example.com/registry.json")

        assert result == ()


# ---------------------------------------------------------------------------
# list_remote
# ---------------------------------------------------------------------------


class TestListRemote:
    def test_delegates_to_fetch_manifest(self):
        entry = _make_entry()
        body = _manifest_json([entry])
        resp = MagicMock()
        resp.read.return_value = body
        resp.__enter__ = lambda s: s
        resp.__exit__ = MagicMock(return_value=False)

        with patch("eigenhelm.registry.urllib.request.urlopen", return_value=resp):
            result = list_remote("https://example.com/registry.json")

        assert len(result) == 1


# ---------------------------------------------------------------------------
# list_local
# ---------------------------------------------------------------------------


class TestListLocal:
    def test_returns_bundled_models(self):
        """Should find at least the bundled models from the package."""
        result = list_local()
        # The project has bundled models — at least one should appear
        assert isinstance(result, tuple)
        # All bundled models should have bundled=True
        bundled = [m for m in result if m.bundled]
        assert len(bundled) >= 1

    def test_includes_cached_models(self, tmp_path):
        """Downloaded models in cache dir should appear."""
        cache_dir = tmp_path / "models"
        cache_dir.mkdir()
        (cache_dir / "custom-model.npz").write_bytes(b"fake npz")

        with patch("eigenhelm.registry._get_cache_dir", return_value=cache_dir):
            result = list_local()

        names = [m.name for m in result]
        assert "custom-model" in names
        custom = [m for m in result if m.name == "custom-model"][0]
        assert custom.bundled is False

    def test_no_duplicates_between_bundled_and_cached(self, tmp_path):
        """If a bundled model name also exists in cache, only bundled version appears."""
        # Get the actual bundled model names
        bundled = [m for m in list_local() if m.bundled]
        if not bundled:
            pytest.skip("No bundled models available")

        cache_dir = tmp_path / "models"
        cache_dir.mkdir()
        # Create a cached file with the same name as a bundled model
        (cache_dir / f"{bundled[0].name}.npz").write_bytes(b"fake npz")

        with patch("eigenhelm.registry._get_cache_dir", return_value=cache_dir):
            result = list_local()

        matching = [m for m in result if m.name == bundled[0].name]
        assert len(matching) == 1
        assert matching[0].bundled is True

    def test_handles_missing_bundled_package(self, tmp_path):
        """Gracefully handles importlib.resources failure."""
        cache_dir = tmp_path / "models"
        # No cache dir exists either

        with (
            patch("eigenhelm.registry._get_cache_dir", return_value=cache_dir),
            patch("importlib.resources.files", side_effect=ModuleNotFoundError("nope")),
        ):
            result = list_local()

        assert result == ()


# ---------------------------------------------------------------------------
# pull_model
# ---------------------------------------------------------------------------


class TestPullModel:
    def _mock_manifest(self, entries):
        body = _manifest_json([_make_entry(**e) for e in entries])
        resp = MagicMock()
        resp.read.return_value = body
        resp.__enter__ = lambda s: s
        resp.__exit__ = MagicMock(return_value=False)
        return resp

    def test_model_not_found(self):
        manifest_resp = self._mock_manifest([{"name": "other-model"}])

        with patch(
            "eigenhelm.registry.urllib.request.urlopen", return_value=manifest_resp
        ):
            with pytest.raises(RegistryError, match="not found in registry"):
                pull_model("nonexistent", "https://example.com/registry.json")

    def test_successful_download(self, tmp_path):
        content = b"fake npz content"
        sha = hashlib.sha256(content).hexdigest()
        entry_data = {"name": "dl-model", "sha256": sha}
        manifest_resp = self._mock_manifest([entry_data])

        dl_resp = MagicMock()
        dl_resp.read.side_effect = [content, b""]
        dl_resp.__enter__ = lambda s: s
        dl_resp.__exit__ = MagicMock(return_value=False)

        cache_dir = tmp_path / "cache"

        call_count = [0]

        def mock_urlopen(url, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return manifest_resp
            return dl_resp

        with (
            patch(
                "eigenhelm.registry.urllib.request.urlopen", side_effect=mock_urlopen
            ),
            patch("eigenhelm.registry._get_cache_dir", return_value=cache_dir),
            patch("eigenhelm.registry.shutil.copyfileobj") as mock_copy,
        ):            # We need the tmp file to have the right hash after copyfileobj
            def write_content(src, dst):
                dst.write(content)

            mock_copy.side_effect = write_content

            result = pull_model("dl-model", "https://example.com/registry.json")

        assert result.name == "dl-model.npz"

    def test_already_cached_with_matching_hash(self, tmp_path):
        content = b"cached npz content"
        sha = hashlib.sha256(content).hexdigest()
        entry_data = {"name": "cached-model", "sha256": sha}
        manifest_resp = self._mock_manifest([entry_data])

        cache_dir = tmp_path / "cache"
        cache_dir.mkdir(parents=True)
        cached_file = cache_dir / "cached-model.npz"
        cached_file.write_bytes(content)

        with (
            patch(
                "eigenhelm.registry.urllib.request.urlopen", return_value=manifest_resp
            ),
            patch("eigenhelm.registry._get_cache_dir", return_value=cache_dir),
        ):
            result = pull_model("cached-model", "https://example.com/registry.json")

        assert result == cached_file

    def test_cached_with_hash_mismatch_redownloads(self, tmp_path):
        """If cached file has wrong hash, it should redownload."""
        old_content = b"old content"
        new_content = b"new content"
        sha = hashlib.sha256(new_content).hexdigest()
        entry_data = {"name": "stale-model", "sha256": sha}
        manifest_resp = self._mock_manifest([entry_data])

        cache_dir = tmp_path / "cache"
        cache_dir.mkdir(parents=True)
        cached_file = cache_dir / "stale-model.npz"
        cached_file.write_bytes(old_content)

        dl_resp = MagicMock()
        dl_resp.__enter__ = lambda s: s
        dl_resp.__exit__ = MagicMock(return_value=False)

        call_count = [0]

        def mock_urlopen(url, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return manifest_resp
            return dl_resp

        with (
            patch(
                "eigenhelm.registry.urllib.request.urlopen", side_effect=mock_urlopen
            ),
            patch("eigenhelm.registry._get_cache_dir", return_value=cache_dir),
            patch("eigenhelm.registry.shutil.copyfileobj") as mock_copy,
        ):
            def write_content(src, dst):
                dst.write(new_content)

            mock_copy.side_effect = write_content

            result = pull_model("stale-model", "https://example.com/registry.json")

        assert result.name == "stale-model.npz"

    def test_download_failure(self, tmp_path):
        entry_data = {"name": "fail-model"}
        manifest_resp = self._mock_manifest([entry_data])

        call_count = [0]

        def mock_urlopen(url, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return manifest_resp
            raise ConnectionError("download failed")

        cache_dir = tmp_path / "cache"

        with (
            patch(
                "eigenhelm.registry.urllib.request.urlopen", side_effect=mock_urlopen
            ),
            patch("eigenhelm.registry._get_cache_dir", return_value=cache_dir),
        ):
            with pytest.raises(RegistryError, match="Download failed"):
                pull_model("fail-model", "https://example.com/registry.json")

    def test_sha256_mismatch_after_download(self, tmp_path):
        bad_content = b"corrupted"
        sha = "0" * 64  # Won't match
        entry_data = {"name": "corrupt-model", "sha256": sha}
        manifest_resp = self._mock_manifest([entry_data])

        dl_resp = MagicMock()
        dl_resp.__enter__ = lambda s: s
        dl_resp.__exit__ = MagicMock(return_value=False)

        call_count = [0]

        def mock_urlopen(url, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return manifest_resp
            return dl_resp

        cache_dir = tmp_path / "cache"

        with (
            patch(
                "eigenhelm.registry.urllib.request.urlopen", side_effect=mock_urlopen
            ),
            patch("eigenhelm.registry._get_cache_dir", return_value=cache_dir),
            patch("eigenhelm.registry.shutil.copyfileobj") as mock_copy,
        ):
            def write_content(src, dst):
                dst.write(bad_content)

            mock_copy.side_effect = write_content

            with pytest.raises(RegistryError, match="SHA256 mismatch"):
                pull_model("corrupt-model", "https://example.com/registry.json")

    def test_force_redownload(self, tmp_path):
        """force=True should download even when cached file has correct hash."""
        content = b"valid content"
        sha = hashlib.sha256(content).hexdigest()
        entry_data = {"name": "force-model", "sha256": sha}
        manifest_resp = self._mock_manifest([entry_data])

        cache_dir = tmp_path / "cache"
        cache_dir.mkdir(parents=True)
        cached_file = cache_dir / "force-model.npz"
        cached_file.write_bytes(content)

        dl_resp = MagicMock()
        dl_resp.__enter__ = lambda s: s
        dl_resp.__exit__ = MagicMock(return_value=False)

        call_count = [0]

        def mock_urlopen(url, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return manifest_resp
            return dl_resp

        with (
            patch(
                "eigenhelm.registry.urllib.request.urlopen", side_effect=mock_urlopen
            ),
            patch("eigenhelm.registry._get_cache_dir", return_value=cache_dir),
            patch("eigenhelm.registry.shutil.copyfileobj") as mock_copy,
        ):
            def write_content(src, dst):
                dst.write(content)

            mock_copy.side_effect = write_content

            result = pull_model(
                "force-model", "https://example.com/registry.json", force=True
            )

        assert result.name == "force-model.npz"


# ---------------------------------------------------------------------------
# resolve_model
# ---------------------------------------------------------------------------


class TestResolveModel:
    def test_finds_bundled_model(self):
        local = list_local()
        if not local:
            pytest.skip("No local models")
        result = resolve_model(local[0].name)
        assert result is not None
        assert result.exists()

    def test_returns_none_for_unknown(self):
        result = resolve_model("definitely-not-a-real-model-xyz")
        assert result is None


# ---------------------------------------------------------------------------
# _find_entry
# ---------------------------------------------------------------------------


class TestFindEntry:
    def test_finds_matching(self):
        entries = (
            ModelEntry(**_make_entry(name="a")),
            ModelEntry(**_make_entry(name="b")),
        )
        assert _find_entry("b", entries).name == "b"

    def test_returns_none_when_no_match(self):
        entries = (ModelEntry(**_make_entry(name="a")),)
        assert _find_entry("z", entries) is None


# ---------------------------------------------------------------------------
# _sha256_file
# ---------------------------------------------------------------------------


class TestSha256File:
    def test_computes_correct_hash(self, tmp_path):
        content = b"hello world"
        f = tmp_path / "test.bin"
        f.write_bytes(content)
        expected = hashlib.sha256(content).hexdigest()
        assert _sha256_file(f) == expected

    def test_empty_file(self, tmp_path):
        f = tmp_path / "empty.bin"
        f.write_bytes(b"")
        expected = hashlib.sha256(b"").hexdigest()
        assert _sha256_file(f) == expected

"""Contract tests for ICorpusSync — eigenhelm.corpus.sync.

All 10 scenarios from contracts/icorpus_sync.md.
All tests use a synthetic in-memory .tar.gz served by a mocked urlopen.
Zero live network calls.
"""

from __future__ import annotations

import gzip
import io
import json
import tarfile
import textwrap
from unittest.mock import MagicMock, patch

import pytest
from eigenhelm.corpus.manifest import CorpusManifest, CorpusTarget

# ---------------------------------------------------------------------------
# Helpers: synthetic tar.gz builder
# ---------------------------------------------------------------------------


def _make_tarball(files: dict[str, bytes], prefix: str = "repo-0.1") -> bytes:
    """Build an in-memory .tar.gz with files under a top-level prefix directory."""
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb") as gz:
        with tarfile.open(fileobj=gz, mode="w") as tf:
            for path, content in files.items():
                full_path = f"{prefix}/{path}"
                info = tarfile.TarInfo(name=full_path)
                info.size = len(content)
                tf.addfile(info, io.BytesIO(content))
    return buf.getvalue()


def _mock_urlopen(tarball: bytes):
    """Return a context-manager mock that serves tarball bytes as an HTTP response."""
    response = MagicMock()
    response.read = MagicMock(side_effect=io.BytesIO(tarball).read)
    response.__enter__ = MagicMock(return_value=io.BytesIO(tarball))
    response.__exit__ = MagicMock(return_value=False)
    return response


def _make_manifest(*targets: CorpusTarget) -> CorpusManifest:
    return CorpusManifest(
        name="test",
        version="1.0.0",
        corpus_class="B",
        created="2026-03-04",
        targets=targets,
    )


def _make_target(
    name: str = "lib",
    include: tuple[str, ...] = ("lib/**/*.py",),
    exclude: tuple[str, ...] = (),
    ref: str = "1.0.0",
) -> CorpusTarget:
    return CorpusTarget(
        name=name,
        url=f"https://github.com/example/{name}",
        ref=ref,
        include=include,
        exclude=exclude,
        description="Test target.",
    )


def _serve(tarball: bytes):
    """Patch urllib.request.urlopen to serve tarball."""
    return patch(
        "eigenhelm.corpus.sync.urllib.request.urlopen",
        return_value=io.BytesIO(tarball),
    )


# ---------------------------------------------------------------------------
# Scenario 1: include filtering — extracts only include-matched files
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_include_filtering(tmp_path):
    from eigenhelm.corpus.sync import sync_manifest

    tarball = _make_tarball(
        {
            "lib/foo.py": b"print('foo')",
            "tests/test_foo.py": b"def test(): pass",
            "README.md": b"# readme",
        }
    )
    target = _make_target(include=("lib/**/*.py",), exclude=())
    manifest = _make_manifest(target)

    with _serve(tarball):
        result = sync_manifest(manifest, tmp_path)

    assert result.synced == ["lib"]
    assert result.failed == []
    py_files = list((tmp_path / "lib").rglob("*.py"))
    assert any(f.name == "foo.py" for f in py_files)
    assert not (tmp_path / "lib" / "tests").exists()
    assert not (tmp_path / "lib" / "README.md").exists()


# ---------------------------------------------------------------------------
# Scenario 2: exclude overrides include
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_exclude_overrides_include(tmp_path):
    from eigenhelm.corpus.sync import sync_manifest

    tarball = _make_tarball(
        {
            "lib/foo.py": b"# lib source",
            "tests/test_foo.py": b"# test",
        }
    )
    target = _make_target(include=("**/*.py",), exclude=("tests/**",))
    manifest = _make_manifest(target)

    with _serve(tarball):
        result = sync_manifest(manifest, tmp_path)

    assert "lib" in result.synced
    assert (tmp_path / "lib" / "lib" / "foo.py").exists()
    assert not (tmp_path / "lib" / "tests").exists()


# ---------------------------------------------------------------------------
# Scenario 3: sentinel written after successful sync
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_sentinel_written_after_successful_sync(tmp_path):
    from eigenhelm.corpus.sync import sync_manifest

    tarball = _make_tarball({"lib/foo.py": b"# src"})
    target = _make_target()
    manifest = _make_manifest(target)

    with _serve(tarball):
        sync_manifest(manifest, tmp_path)

    sentinel_path = tmp_path / "lib" / ".eigenhelm-sync"
    assert sentinel_path.exists()
    data = json.loads(sentinel_path.read_text())
    assert data["schema_version"] == 1
    assert data["ref"] == "1.0.0"
    assert data["entry_hash"] == target.entry_hash()
    assert data["files_extracted"] >= 1


# ---------------------------------------------------------------------------
# Scenario 4: already-synced target is skipped
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_already_synced_target_is_skipped(tmp_path):
    from eigenhelm.corpus.sync import sync_manifest

    tarball = _make_tarball({"lib/foo.py": b"# src"})
    target = _make_target()
    manifest = _make_manifest(target)

    with _serve(tarball):
        sync_manifest(manifest, tmp_path)

    # Second run — urlopen must NOT be called
    with patch("eigenhelm.corpus.sync.urllib.request.urlopen") as mock_open:
        result = sync_manifest(manifest, tmp_path)

    mock_open.assert_not_called()
    assert result.skipped == ["lib"]
    assert result.synced == []


# ---------------------------------------------------------------------------
# Scenario 5: changed include patterns trigger re-sync
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_changed_patterns_trigger_resync(tmp_path):
    from eigenhelm.corpus.sync import sync_manifest

    tarball = _make_tarball({"lib/foo.py": b"# src"})
    target_v1 = _make_target(include=("lib/**/*.py",))
    manifest_v1 = _make_manifest(target_v1)

    with _serve(tarball):
        sync_manifest(manifest_v1, tmp_path)

    # Change include patterns
    target_v2 = _make_target(include=("lib/**/*.py", "lib/**/*.pyi"))
    manifest_v2 = _make_manifest(target_v2)

    with _serve(tarball) as mock_open:
        result = sync_manifest(manifest_v2, tmp_path)

    mock_open.assert_called_once()
    assert result.synced == ["lib"]


# ---------------------------------------------------------------------------
# Scenario 6: network failure captured in SyncResult.failed
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_network_failure_captured_in_failed(tmp_path):
    import urllib.error

    from eigenhelm.corpus.sync import sync_manifest

    tarball = _make_tarball({"other/foo.py": b"# src"})
    failing = _make_target(name="failing")
    ok_target = CorpusTarget(
        name="other",
        url="https://github.com/example/other",
        ref="1.0.0",
        include=("other/**/*.py",),
        exclude=(),
        description="Works fine.",
    )
    manifest = _make_manifest(failing, ok_target)

    def selective_urlopen(req):
        if "failing" in req.full_url:
            raise urllib.error.URLError("connection refused")
        return io.BytesIO(tarball)

    with patch("eigenhelm.corpus.sync.urllib.request.urlopen", side_effect=selective_urlopen):
        result = sync_manifest(manifest, tmp_path)

    assert len(result.failed) == 1
    assert result.failed[0][0] == "failing"
    assert result.synced == ["other"]


# ---------------------------------------------------------------------------
# Scenario 7: all failed → CLI exits with code 2
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_all_failed_cli_exits_2(tmp_path, monkeypatch):
    import urllib.error

    monkeypatch.chdir(tmp_path)

    # Write a minimal manifest file
    toml_path = tmp_path / "test.toml"
    toml_path.write_text(
        textwrap.dedent("""\
        [corpus]
        name = "test"
        version = "1.0.0"
        class = "B"
        created = "2026-03-04"

        [[target]]
        name = "lib"
        url = "https://github.com/example/lib"
        ref = "1.0.0"
        include = ["lib/**/*.py"]
        description = "Test."
    """)
    )
    out_dir = tmp_path / "out"

    with patch(
        "eigenhelm.corpus.sync.urllib.request.urlopen",
        side_effect=urllib.error.URLError("timeout"),
    ):
        with pytest.raises(SystemExit) as exc_info:
            from eigenhelm.cli.corpus import main

            main(["sync", str(toml_path), str(out_dir)])

    assert exc_info.value.code == 2


# ---------------------------------------------------------------------------
# Scenario 8: --force re-downloads even when sentinel present
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_force_redownloads_when_sentinel_present(tmp_path):
    from eigenhelm.corpus.sync import sync_manifest

    tarball = _make_tarball({"lib/foo.py": b"# src"})
    target = _make_target()
    manifest = _make_manifest(target)

    with _serve(tarball):
        sync_manifest(manifest, tmp_path)

    with _serve(tarball) as mock_open:
        result = sync_manifest(manifest, tmp_path, force=True)

    mock_open.assert_called_once()
    assert result.synced == ["lib"]


# ---------------------------------------------------------------------------
# Scenario 9: top-level directory stripped from archive paths
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_top_level_directory_stripped(tmp_path):
    from eigenhelm.corpus.sync import sync_manifest

    # Archive wraps files in "lib-1.0.0/" top-level dir
    tarball = _make_tarball(
        {"lib/_client.py": b"# client"},
        prefix="lib-1.0.0",
    )
    target = _make_target(include=("lib/**/*.py",))
    manifest = _make_manifest(target)

    with _serve(tarball):
        sync_manifest(manifest, tmp_path)

    # File should be at tmp_path/lib/lib/_client.py (not .../lib-1.0.0/lib/_client.py)
    extracted = tmp_path / "lib" / "lib" / "_client.py"
    found = list((tmp_path / "lib").rglob("*.py"))
    assert extracted.exists(), f"expected {extracted}, got: {found}"


# ---------------------------------------------------------------------------
# Scenario 10: changed ref emits named warning before re-sync
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_changed_ref_emits_named_warning(tmp_path):
    import warnings

    from eigenhelm.corpus.sync import sync_manifest

    tarball = _make_tarball({"lib/foo.py": b"# src"})
    target_v1 = _make_target(ref="1.0.0")
    manifest_v1 = _make_manifest(target_v1)

    with _serve(tarball):
        sync_manifest(manifest_v1, tmp_path)

    target_v2 = _make_target(ref="2.0.0")
    manifest_v2 = _make_manifest(target_v2)

    with _serve(tarball):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = sync_manifest(manifest_v2, tmp_path)

    assert result.synced == ["lib"]
    warning_messages = [str(w.message) for w in caught]
    combined = " ".join(warning_messages)
    assert "1.0.0" in combined, f"old ref '1.0.0' not in warnings: {combined}"
    assert "2.0.0" in combined, f"new ref '2.0.0' not in warnings: {combined}"


# ---------------------------------------------------------------------------
# Scenario 11: Path traversal protection — skip members escaping dest_dir
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_path_traversal_protection(tmp_path):
    import warnings

    from eigenhelm.corpus.sync import sync_manifest

    # Malicious tarball with a path escaping the repo-1.0.0 prefix
    # After stripping repo-1.0.0, it becomes ../escaping.py
    tarball = _make_tarball(
        {"../escaping.py": b"print('hacked')"},
        prefix="repo-1.0.0",
    )
    target = _make_target(include=("**/*.py",))
    manifest = _make_manifest(target)

    with _serve(tarball):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = sync_manifest(manifest, tmp_path)

    # Should be skipped, not failed
    assert result.synced == ["lib"]
    assert result.failed == []
    assert not (tmp_path / "escaping.py").exists()
    assert any("potential path traversal" in str(w.message) for w in caught)


# ---------------------------------------------------------------------------
# Bulk sync: discover_manifests
# ---------------------------------------------------------------------------


def _write_corpus_toml(directory, name, target_name="lib"):
    """Write a minimal valid corpus manifest."""
    content = textwrap.dedent(f"""\
        [corpus]
        name = "{name}"
        version = "1.0.0"
        class = "B"
        created = "2026-03-06"

        [[target]]
        name = "{target_name}"
        url = "https://github.com/example/{target_name}"
        ref = "1.0.0"
        include = ["lib/**/*.py"]
        description = "Test target."
    """)
    path = directory / f"{name}.toml"
    path.write_text(content)
    return path


def _write_composition_toml(directory, name, sources):
    """Write a minimal valid composition manifest."""
    src_list = ", ".join(f'"{s}"' for s in sources)
    content = textwrap.dedent(f"""\
        [composition]
        name = "{name}"
        version = "1.0.0"
        created = "2026-03-06"
        sources = [{src_list}]
    """)
    path = directory / f"{name}.toml"
    path.write_text(content)
    return path


@pytest.mark.contract
def test_discover_manifests_finds_corpus_toml(tmp_path):
    from eigenhelm.corpus.sync import discover_manifests

    _write_corpus_toml(tmp_path, "lang-python", "httpx")
    _write_corpus_toml(tmp_path, "lang-go", "gjson")

    paths = discover_manifests(tmp_path)
    names = [p.name for p in paths]
    assert "lang-python.toml" in names
    assert "lang-go.toml" in names


@pytest.mark.contract
def test_discover_manifests_skips_composition(tmp_path):
    import warnings

    from eigenhelm.corpus.sync import discover_manifests

    _write_corpus_toml(tmp_path, "lang-python", "httpx")
    _write_composition_toml(tmp_path, "training", ["lang-python.toml"])

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        paths = discover_manifests(tmp_path)

    names = [p.name for p in paths]
    assert "lang-python.toml" in names
    assert "training.toml" not in names
    assert any("composition" in str(w.message) for w in caught)


@pytest.mark.contract
def test_discover_manifests_skips_non_manifest(tmp_path):
    import warnings

    from eigenhelm.corpus.sync import discover_manifests

    _write_corpus_toml(tmp_path, "lang-python", "httpx")
    (tmp_path / "garbage.toml").write_text("not valid [[[ toml stuff")

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        paths = discover_manifests(tmp_path)

    names = [p.name for p in paths]
    assert "lang-python.toml" in names
    assert "garbage.toml" not in names
    assert any("unparseable" in str(w.message) for w in caught)


# ---------------------------------------------------------------------------
# Bulk sync: sync_all_manifests
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_sync_all_manifests_syncs_multiple(tmp_path):
    from eigenhelm.corpus.sync import sync_all_manifests

    corpora_dir = tmp_path / "corpora"
    corpora_dir.mkdir()
    _write_corpus_toml(corpora_dir, "lang-a", "alpha")
    _write_corpus_toml(corpora_dir, "lang-b", "beta")

    tarball_a = _make_tarball({"lib/a.py": b"# alpha"})
    tarball_b = _make_tarball({"lib/b.py": b"# beta"})

    def selective_urlopen(req):
        if "alpha" in req.full_url:
            return io.BytesIO(tarball_a)
        return io.BytesIO(tarball_b)

    out = tmp_path / "output"
    with patch(
        "eigenhelm.corpus.sync.urllib.request.urlopen",
        side_effect=selective_urlopen,
    ):
        bulk = sync_all_manifests(corpora_dir, out)

    assert len(bulk.per_manifest) == 2
    assert not bulk.any_failed


@pytest.mark.contract
def test_sync_all_idempotent(tmp_path):
    from eigenhelm.corpus.sync import sync_all_manifests

    corpora_dir = tmp_path / "corpora"
    corpora_dir.mkdir()
    _write_corpus_toml(corpora_dir, "lang-a", "alpha")

    tarball = _make_tarball({"lib/a.py": b"# alpha"})
    out = tmp_path / "output"

    with _serve(tarball):
        sync_all_manifests(corpora_dir, out)

    # Second run — should skip
    with patch("eigenhelm.corpus.sync.urllib.request.urlopen") as mock_open:
        bulk = sync_all_manifests(corpora_dir, out)

    mock_open.assert_not_called()
    for sr in bulk.per_manifest.values():
        assert sr.synced == []
        assert sr.skipped == ["alpha"]


@pytest.mark.contract
def test_sync_all_partial_failure(tmp_path):
    import urllib.error

    from eigenhelm.corpus.sync import sync_all_manifests

    corpora_dir = tmp_path / "corpora"
    corpora_dir.mkdir()
    _write_corpus_toml(corpora_dir, "lang-a", "alpha")
    # Write a valid manifest but make its target URL fail
    _write_corpus_toml(corpora_dir, "lang-b", "broken")

    tarball = _make_tarball({"lib/a.py": b"# alpha"})

    def selective_urlopen(req):
        if "broken" in req.full_url:
            raise urllib.error.URLError("connection refused")
        return io.BytesIO(tarball)

    out = tmp_path / "output"
    with patch(
        "eigenhelm.corpus.sync.urllib.request.urlopen",
        side_effect=selective_urlopen,
    ):
        bulk = sync_all_manifests(corpora_dir, out)

    assert bulk.any_failed
    # lang-a should succeed
    assert "lang-a" in bulk.per_manifest
    assert bulk.per_manifest["lang-a"].synced == ["alpha"]


# ---------------------------------------------------------------------------
# Composition sync
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_sync_composition_materializes_sources(tmp_path):
    from eigenhelm.corpus.manifest import CompositionManifest
    from eigenhelm.corpus.sync import sync_composition

    corpora_dir = tmp_path / "corpora"
    corpora_dir.mkdir()
    _write_corpus_toml(corpora_dir, "lang-a", "alpha")
    _write_corpus_toml(corpora_dir, "lang-b", "beta")

    comp = CompositionManifest(
        name="training",
        version="1.0.0",
        created="2026-03-06",
        sources=("lang-a.toml", "lang-b.toml"),
    )

    tarball_a = _make_tarball({"lib/a.py": b"# alpha"})
    tarball_b = _make_tarball({"lib/b.py": b"# beta"})

    def selective_urlopen(req):
        if "alpha" in req.full_url:
            return io.BytesIO(tarball_a)
        return io.BytesIO(tarball_b)

    out = tmp_path / "output"
    with patch(
        "eigenhelm.corpus.sync.urllib.request.urlopen",
        side_effect=selective_urlopen,
    ):
        bulk = sync_composition(comp, corpora_dir, out)

    assert "lang-a" in bulk.per_manifest
    assert "lang-b" in bulk.per_manifest
    assert not bulk.any_failed
    # Each source gets own subdirectory
    assert (out / "lang-a").exists()
    assert (out / "lang-b").exists()


@pytest.mark.contract
def test_sync_composition_missing_source(tmp_path):
    from eigenhelm.corpus.manifest import CompositionManifest
    from eigenhelm.corpus.sync import sync_composition

    corpora_dir = tmp_path / "corpora"
    corpora_dir.mkdir()

    comp = CompositionManifest(
        name="training",
        version="1.0.0",
        created="2026-03-06",
        sources=("missing.toml",),
    )

    out = tmp_path / "output"
    with pytest.raises(FileNotFoundError, match="missing.toml"):
        sync_composition(comp, corpora_dir, out)

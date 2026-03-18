"""Unit tests for CorpusTarget validation, archive_url, and entry_hash().

Written FIRST (TDD) — must fail before manifest.py is implemented.
"""

from __future__ import annotations

import tomllib

import pytest

# ---------------------------------------------------------------------------
# CorpusTarget validation
# ---------------------------------------------------------------------------


def _make_target(**kwargs):
    from eigenhelm.corpus.manifest import CorpusTarget

    defaults = dict(
        name="httpx",
        url="https://github.com/encode/httpx",
        ref="0.28.1",
        include=("httpx/**/*.py",),
        exclude=(),
        description="Async HTTP client.",
    )
    defaults.update(kwargs)
    return CorpusTarget(**defaults)


def test_valid_target_constructs():
    t = _make_target()
    assert t.name == "httpx"
    assert t.ref == "0.28.1"
    assert t.include == ("httpx/**/*.py",)
    assert t.exclude == ()


def test_empty_name_raises():
    with pytest.raises(ValueError, match="name"):
        _make_target(name="")


def test_url_not_https_raises():
    with pytest.raises(ValueError, match="https://"):
        _make_target(url="http://github.com/encode/httpx")


def test_empty_url_raises():
    with pytest.raises(ValueError, match="url"):
        _make_target(url="")


def test_empty_ref_raises():
    with pytest.raises(ValueError, match="ref"):
        _make_target(ref="")


def test_empty_include_list_raises():
    with pytest.raises(ValueError, match="include"):
        _make_target(include=())


def test_empty_string_in_include_raises():
    with pytest.raises(ValueError, match="include"):
        _make_target(include=("httpx/**/*.py", ""))


def test_empty_string_in_exclude_raises():
    with pytest.raises(ValueError, match="exclude"):
        _make_target(exclude=("tests/**", ""))


def test_empty_description_raises():
    with pytest.raises(ValueError, match="description"):
        _make_target(description="")


# ---------------------------------------------------------------------------
# archive_url — tag ref vs SHA ref
# ---------------------------------------------------------------------------


def test_archive_url_tag_ref():
    t = _make_target(url="https://github.com/encode/httpx", ref="0.28.1")
    assert t.archive_url == "https://github.com/encode/httpx/archive/refs/tags/0.28.1.tar.gz"


def test_archive_url_tag_ref_with_v_prefix():
    t = _make_target(url="https://github.com/pydantic/pydantic", ref="v2.12.5")
    assert t.archive_url == "https://github.com/pydantic/pydantic/archive/refs/tags/v2.12.5.tar.gz"


def test_archive_url_sha_ref():
    sha = "a" * 40
    t = _make_target(url="https://github.com/encode/httpx", ref=sha)
    assert t.archive_url == f"https://github.com/encode/httpx/archive/{sha}.tar.gz"


def test_archive_url_39_char_hex_is_tag():
    # 39 hex chars is NOT a SHA — treated as tag
    ref_39 = "a" * 39
    t = _make_target(ref=ref_39)
    assert "/refs/tags/" in t.archive_url


def test_archive_url_mixed_case_sha():
    sha = "A" * 40  # uppercase hex — should still be recognized as SHA
    t = _make_target(ref=sha)
    assert "/refs/tags/" not in t.archive_url


# ---------------------------------------------------------------------------
# entry_hash
# ---------------------------------------------------------------------------


def test_entry_hash_returns_sha256_prefix():
    t = _make_target()
    h = t.entry_hash()
    assert h.startswith("sha256:")
    assert len(h) == len("sha256:") + 64


def test_entry_hash_is_deterministic():
    t1 = _make_target()
    t2 = _make_target()
    assert t1.entry_hash() == t2.entry_hash()


def test_entry_hash_changes_on_ref_change():
    t1 = _make_target(ref="0.28.1")
    t2 = _make_target(ref="0.28.2")
    assert t1.entry_hash() != t2.entry_hash()


def test_entry_hash_changes_on_include_change():
    t1 = _make_target(include=("httpx/**/*.py",))
    t2 = _make_target(include=("httpx/**/*.py", "httpx/**/*.pyi"))
    assert t1.entry_hash() != t2.entry_hash()


def test_entry_hash_changes_on_exclude_change():
    t1 = _make_target(exclude=())
    t2 = _make_target(exclude=("tests/**",))
    assert t1.entry_hash() != t2.entry_hash()


def test_entry_hash_does_not_include_description():
    # description is not part of the idempotency key
    t1 = _make_target(description="Async HTTP client.")
    t2 = _make_target(description="A different description.")
    assert t1.entry_hash() == t2.entry_hash()


# ---------------------------------------------------------------------------
# CompositionManifest validation
# ---------------------------------------------------------------------------


def _make_composition(**kwargs):
    from eigenhelm.corpus.manifest import CompositionManifest

    defaults = dict(
        name="training",
        version="1.0.0",
        created="2026-03-06",
        sources=("lang-python.toml", "lang-javascript.toml"),
    )
    defaults.update(kwargs)
    return CompositionManifest(**defaults)


def test_valid_composition_constructs():
    c = _make_composition()
    assert c.name == "training"
    assert c.sources == ("lang-python.toml", "lang-javascript.toml")


def test_composition_empty_name_raises():
    with pytest.raises(ValueError, match="name"):
        _make_composition(name="")


def test_composition_empty_version_raises():
    with pytest.raises(ValueError, match="version"):
        _make_composition(version="")


def test_composition_empty_created_raises():
    with pytest.raises(ValueError, match="created"):
        _make_composition(created="")


def test_composition_empty_sources_raises():
    with pytest.raises(ValueError, match="sources"):
        _make_composition(sources=())


def test_composition_empty_string_in_sources_raises():
    with pytest.raises(ValueError, match="empty"):
        _make_composition(sources=("lang-python.toml", ""))


def test_composition_non_toml_source_raises():
    with pytest.raises(ValueError, match=".toml"):
        _make_composition(sources=("lang-python.txt",))


# ---------------------------------------------------------------------------
# load_any_manifest dispatch
# ---------------------------------------------------------------------------


def test_load_any_manifest_returns_corpus_for_corpus_toml(tmp_path):
    from eigenhelm.corpus.manifest import CorpusManifest, load_any_manifest

    toml = (
        '[corpus]\nname = "test"\nversion = "1"'
        '\nlanguage = "python"\nclass = "A"\ncreated = "2026"'
        '\n\n[[target]]\nname = "x"'
        '\nurl = "https://github.com/a/b"\nref = "1.0"'
        '\ninclude = ["*.py"]\ndescription = "Test."'
    )
    p = tmp_path / "corpus.toml"
    p.write_text(toml)
    result = load_any_manifest(p)
    assert isinstance(result, CorpusManifest)


def test_load_any_manifest_returns_composition_for_composition_toml(tmp_path):
    from eigenhelm.corpus.manifest import CompositionManifest, load_any_manifest

    toml = '[composition]\nname = "training"\nversion = "1"\ncreated = "2026"\nsources = ["a.toml"]'
    p = tmp_path / "comp.toml"
    p.write_text(toml)
    result = load_any_manifest(p)
    assert isinstance(result, CompositionManifest)


def test_load_any_manifest_raises_on_unknown_header(tmp_path):
    from eigenhelm.corpus.manifest import load_any_manifest

    toml = '[unknown]\nfoo = "bar"'
    p = tmp_path / "bad.toml"
    p.write_text(toml)
    with pytest.raises(ValueError, match="neither"):
        load_any_manifest(p)


# ---------------------------------------------------------------------------
# CompositionManifest.resolve()
# ---------------------------------------------------------------------------


def test_resolve_loads_valid_sources(tmp_path):
    from eigenhelm.corpus.manifest import CompositionManifest

    corpus_toml = (
        '[corpus]\nname = "test"\nversion = "1"'
        '\nlanguage = "python"\nclass = "A"\ncreated = "2026"'
        '\n\n[[target]]\nname = "x"'
        '\nurl = "https://github.com/a/b"\nref = "1.0"'
        '\ninclude = ["*.py"]\ndescription = "Test."'
    )
    (tmp_path / "a.toml").write_text(corpus_toml)
    comp = CompositionManifest(
        name="test", version="1", created="2026", sources=("a.toml",)
    )
    manifests = comp.resolve(tmp_path)
    assert len(manifests) == 1
    assert manifests[0].name == "test"


def test_resolve_raises_on_missing_source(tmp_path):
    from eigenhelm.corpus.manifest import CompositionManifest

    comp = CompositionManifest(
        name="test", version="1", created="2026", sources=("missing.toml",)
    )
    with pytest.raises(FileNotFoundError):
        comp.resolve(tmp_path)


def test_resolve_raises_on_invalid_toml(tmp_path):
    from eigenhelm.corpus.manifest import CompositionManifest

    (tmp_path / "bad.toml").write_text("not valid [[[toml")
    comp = CompositionManifest(
        name="test", version="1", created="2026", sources=("bad.toml",)
    )
    with pytest.raises(tomllib.TOMLDecodeError):
        comp.resolve(tmp_path)

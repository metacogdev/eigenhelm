"""Unit tests for CorpusTarget validation, archive_url, and entry_hash().

Written FIRST (TDD) — must fail before manifest.py is implemented.
"""

from __future__ import annotations

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

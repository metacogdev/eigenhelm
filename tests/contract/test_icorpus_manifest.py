"""Contract tests for ICorpusManifest — eigenhelm.corpus.manifest.

Tests the public contract: load_manifest(), CorpusManifest, CorpusTarget.
All 10 scenarios from contracts/icorpus_manifest.md.
Zero network calls.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VALID_TWO_TARGET_TOML = textwrap.dedent("""\
    [corpus]
    name = "test-corpus"
    version = "1.0.0"
    language = "python"
    class = "A"
    created = "2026-03-04"

    [[target]]
    name = "httpx"
    url = "https://github.com/encode/httpx"
    ref = "0.28.1"
    include = ["httpx/**/*.py"]
    exclude = ["tests/**", "docs/**"]
    description = "Async HTTP client."

    [[target]]
    name = "rich"
    url = "https://github.com/Textualize/rich"
    ref = "14.3.3"
    include = ["rich/**/*.py"]
    exclude = ["tests/**"]
    description = "Terminal formatting library."
""")


def write_toml(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "manifest.toml"
    p.write_text(content)
    return p


# ---------------------------------------------------------------------------
# Scenario 1: Round-trip — valid 2-target manifest parses completely
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_round_trip_valid_two_target_manifest(tmp_path):
    from eigenhelm.corpus.manifest import CorpusManifest, CorpusTarget, load_manifest

    path = write_toml(tmp_path, VALID_TWO_TARGET_TOML)
    manifest = load_manifest(path)

    assert isinstance(manifest, CorpusManifest)
    assert manifest.name == "test-corpus"
    assert manifest.version == "1.0.0"
    assert manifest.corpus_class == "A"
    assert manifest.language == "python"
    assert manifest.created == "2026-03-04"
    assert len(manifest.targets) == 2

    httpx = manifest.targets[0]
    assert isinstance(httpx, CorpusTarget)
    assert httpx.name == "httpx"
    assert httpx.url == "https://github.com/encode/httpx"
    assert httpx.ref == "0.28.1"
    assert httpx.include == ("httpx/**/*.py",)
    assert httpx.exclude == ("tests/**", "docs/**")
    assert httpx.description == "Async HTTP client."


# ---------------------------------------------------------------------------
# Scenario 2: Missing required field "ref" raises ValueError
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_missing_ref_raises_value_error(tmp_path):
    from eigenhelm.corpus.manifest import load_manifest

    toml = textwrap.dedent("""\
        [corpus]
        name = "test"
        version = "1.0.0"
        language = "python"
        class = "A"
        created = "2026-03-04"

        [[target]]
        name = "httpx"
        url = "https://github.com/encode/httpx"
        include = ["httpx/**/*.py"]
        description = "HTTP client."
    """)
    path = write_toml(tmp_path, toml)

    with pytest.raises(ValueError) as exc_info:
        load_manifest(path)
    msg = str(exc_info.value).lower()
    assert "ref" in msg
    assert "httpx" in msg


# ---------------------------------------------------------------------------
# Scenario 3: Missing required field "url" raises ValueError
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_missing_url_raises_value_error(tmp_path):
    from eigenhelm.corpus.manifest import load_manifest

    toml = textwrap.dedent("""\
        [corpus]
        name = "test"
        version = "1.0.0"
        language = "python"
        class = "A"
        created = "2026-03-04"

        [[target]]
        name = "httpx"
        ref = "0.28.1"
        include = ["httpx/**/*.py"]
        description = "HTTP client."
    """)
    path = write_toml(tmp_path, toml)

    with pytest.raises(ValueError) as exc_info:
        load_manifest(path)
    assert "url" in str(exc_info.value).lower()


# ---------------------------------------------------------------------------
# Scenario 4: Empty include list raises ValueError
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_empty_include_list_raises_value_error(tmp_path):
    from eigenhelm.corpus.manifest import load_manifest

    toml = textwrap.dedent("""\
        [corpus]
        name = "test"
        version = "1.0.0"
        language = "python"
        class = "A"
        created = "2026-03-04"

        [[target]]
        name = "httpx"
        url = "https://github.com/encode/httpx"
        ref = "0.28.1"
        include = []
        description = "HTTP client."
    """)
    path = write_toml(tmp_path, toml)

    with pytest.raises(ValueError) as exc_info:
        load_manifest(path)
    msg = str(exc_info.value).lower()
    assert "include" in msg
    assert "httpx" in msg


# ---------------------------------------------------------------------------
# Scenario 5: Empty-string pattern in include raises ValueError
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_empty_string_pattern_in_include_raises(tmp_path):
    from eigenhelm.corpus.manifest import load_manifest

    toml = textwrap.dedent("""\
        [corpus]
        name = "test"
        version = "1.0.0"
        language = "python"
        class = "A"
        created = "2026-03-04"

        [[target]]
        name = "httpx"
        url = "https://github.com/encode/httpx"
        ref = "0.28.1"
        include = ["httpx/**/*.py", ""]
        description = "HTTP client."
    """)
    path = write_toml(tmp_path, toml)

    with pytest.raises(ValueError) as exc_info:
        load_manifest(path)
    assert "include" in str(exc_info.value).lower()


# ---------------------------------------------------------------------------
# Scenario 6: Duplicate target names raises ValueError
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_duplicate_target_names_raises(tmp_path):
    from eigenhelm.corpus.manifest import load_manifest

    toml = textwrap.dedent("""\
        [corpus]
        name = "test"
        version = "1.0.0"
        language = "python"
        class = "A"
        created = "2026-03-04"

        [[target]]
        name = "httpx"
        url = "https://github.com/encode/httpx"
        ref = "0.28.1"
        include = ["httpx/**/*.py"]
        description = "First."

        [[target]]
        name = "httpx"
        url = "https://github.com/encode/httpx"
        ref = "0.28.1"
        include = ["httpx/**/*.py"]
        description = "Duplicate."
    """)
    path = write_toml(tmp_path, toml)

    with pytest.raises(ValueError) as exc_info:
        load_manifest(path)
    msg = str(exc_info.value).lower()
    assert "duplicate" in msg
    assert "httpx" in msg


# ---------------------------------------------------------------------------
# Scenario 7: Missing file raises FileNotFoundError
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_missing_file_raises_file_not_found(tmp_path):
    from eigenhelm.corpus.manifest import load_manifest

    path = tmp_path / "nonexistent.toml"

    with pytest.raises(FileNotFoundError):
        load_manifest(path)


# ---------------------------------------------------------------------------
# Scenario 8: corpus_class must be A, B, or C
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_invalid_corpus_class_raises(tmp_path):
    from eigenhelm.corpus.manifest import load_manifest

    toml = textwrap.dedent("""\
        [corpus]
        name = "test"
        version = "1.0.0"
        class = "D"
        created = "2026-03-04"

        [[target]]
        name = "httpx"
        url = "https://github.com/encode/httpx"
        ref = "0.28.1"
        include = ["httpx/**/*.py"]
        description = "HTTP client."
    """)
    path = write_toml(tmp_path, toml)

    with pytest.raises(ValueError) as exc_info:
        load_manifest(path)
    assert "class" in str(exc_info.value).lower()


# ---------------------------------------------------------------------------
# Scenario 9: archive_url computed correctly
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_archive_url_tag_ref(tmp_path):
    from eigenhelm.corpus.manifest import load_manifest

    path = write_toml(tmp_path, VALID_TWO_TARGET_TOML)
    manifest = load_manifest(path)
    httpx = manifest.targets[0]

    assert httpx.archive_url == "https://github.com/encode/httpx/archive/refs/tags/0.28.1.tar.gz"


# ---------------------------------------------------------------------------
# Scenario 10: No external dependencies
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_no_external_dependencies_at_import():
    """Importing eigenhelm.corpus.manifest must not require tree-sitter, numpy, or scipy."""
    import importlib
    import sys

    # Remove any cached version to force fresh import check
    for key in list(sys.modules.keys()):
        if "eigenhelm.corpus" in key:
            del sys.modules[key]

    # This should succeed with stdlib only
    mod = importlib.import_module("eigenhelm.corpus.manifest")
    assert hasattr(mod, "load_manifest")
    assert hasattr(mod, "CorpusManifest")
    assert hasattr(mod, "CorpusTarget")


# ---------------------------------------------------------------------------
# Additional: language required for class A, optional for class B
# ---------------------------------------------------------------------------


@pytest.mark.contract
def test_class_a_requires_language(tmp_path):
    from eigenhelm.corpus.manifest import load_manifest

    toml = textwrap.dedent("""\
        [corpus]
        name = "test"
        version = "1.0.0"
        class = "A"
        created = "2026-03-04"

        [[target]]
        name = "httpx"
        url = "https://github.com/encode/httpx"
        ref = "0.28.1"
        include = ["httpx/**/*.py"]
        description = "HTTP client."
    """)
    path = write_toml(tmp_path, toml)

    with pytest.raises(ValueError, match="language"):
        load_manifest(path)


@pytest.mark.contract
def test_class_b_language_optional(tmp_path):
    from eigenhelm.corpus.manifest import load_manifest

    toml = textwrap.dedent("""\
        [corpus]
        name = "test"
        version = "1.0.0"
        class = "B"
        created = "2026-03-04"

        [[target]]
        name = "httpx"
        url = "https://github.com/encode/httpx"
        ref = "0.28.1"
        include = ["httpx/**/*.py"]
        description = "HTTP client."
    """)
    path = write_toml(tmp_path, toml)

    manifest = load_manifest(path)
    assert manifest.corpus_class == "B"
    assert manifest.language is None


@pytest.mark.contract
def test_targets_immutable_tuple(tmp_path):
    from eigenhelm.corpus.manifest import load_manifest

    path = write_toml(tmp_path, VALID_TWO_TARGET_TOML)
    manifest = load_manifest(path)

    assert isinstance(manifest.targets, tuple)
    assert isinstance(manifest.targets[0].include, tuple)
    assert isinstance(manifest.targets[0].exclude, tuple)

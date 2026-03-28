"""Validation tests for multi-language corpus manifests (008 User Story 1).

Verifies each of the four new language manifests (JavaScript, TypeScript, Go,
Rust) parses correctly, has all required fields, pins to immutable refs, uses
language-appropriate include/exclude patterns, and includes non-empty rationale
descriptions.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from eigenhelm.corpus.manifest import load_manifest

CORPORA_DIR = Path(__file__).resolve().parents[2] / "corpora"

# Refs that indicate a floating/mutable pointer — must NOT appear.
_MUTABLE_REFS = {"main", "master", "HEAD", "latest", "dev", "develop"}

# Expected language → file extension mapping for include patterns.
_LANG_EXTENSIONS = {
    "javascript": ".js",
    "typescript": ".ts",
    "go": ".go",
    "rust": ".rs",
}

# Language-specific exclude conventions that MUST be present.
_LANG_EXCLUDE_CONVENTIONS: dict[str, list[str]] = {
    "javascript": ["node_modules", "dist", "test"],
    "typescript": ["dist", "*.d.ts", "*.js"],
    "go": ["*_test.go", "vendor", "testdata"],
    "rust": ["tests", "benches", "target"],
}

# Expected target counts per manifest.
_EXPECTED_TARGETS = {
    "javascript": 4,
    "typescript": 3,
    "go": 4,
    "rust": 4,
}

MANIFESTS = list(_EXPECTED_TARGETS.keys())


@pytest.fixture(params=MANIFESTS, ids=MANIFESTS)
def manifest_lang(request: pytest.FixtureRequest) -> str:
    return request.param


@pytest.fixture
def manifest(manifest_lang: str):
    return load_manifest(CORPORA_DIR / f"lang-{manifest_lang}.toml")


class TestManifestMetadata:
    """Verify corpus-level metadata for each manifest."""

    def test_language_matches(self, manifest, manifest_lang):
        assert manifest.language == manifest_lang

    def test_corpus_class_is_a(self, manifest):
        assert manifest.corpus_class == "A"

    def test_name_follows_convention(self, manifest, manifest_lang):
        assert manifest.name == f"lang-{manifest_lang}"

    def test_version_is_set(self, manifest):
        assert manifest.version

    def test_created_is_set(self, manifest):
        assert manifest.created

    def test_expected_target_count(self, manifest, manifest_lang):
        assert len(manifest.targets) == _EXPECTED_TARGETS[manifest_lang]


class TestPinnedRefs:
    """All refs must be pinned to immutable release tags."""

    def test_refs_not_mutable(self, manifest):
        for target in manifest.targets:
            assert target.ref not in _MUTABLE_REFS, (
                f"{target.name}: ref '{target.ref}' is a mutable pointer"
            )

    def test_refs_non_empty(self, manifest):
        for target in manifest.targets:
            assert target.ref, f"{target.name}: ref must be non-empty"


class TestIncludePatterns:
    """Include patterns must target the correct file extension for the language."""

    def test_include_targets_correct_extension(self, manifest, manifest_lang):
        ext = _LANG_EXTENSIONS[manifest_lang]
        for target in manifest.targets:
            assert any(pat.endswith(f"*{ext}") for pat in target.include), (
                f"{target.name}: no include pattern targets *{ext}"
            )


class TestExcludePatterns:
    """Exclude patterns must cover language-specific conventions."""

    def test_exclude_covers_conventions(self, manifest, manifest_lang):
        conventions = _LANG_EXCLUDE_CONVENTIONS[manifest_lang]
        for target in manifest.targets:
            for convention in conventions:
                # Check if the convention appears in any exclude pattern
                found = any(convention in pat for pat in target.exclude)
                assert found, (
                    f"{target.name}: missing exclude convention '{convention}' "
                    f"(has: {target.exclude})"
                )


class TestDescriptions:
    """All description fields must be non-empty and explain structural qualities."""

    def test_descriptions_non_empty(self, manifest):
        for target in manifest.targets:
            assert target.description, f"{target.name}: description must be non-empty"

    def test_descriptions_are_substantial(self, manifest):
        for target in manifest.targets:
            # Descriptions should be more than just a name — at least 30 chars
            assert len(target.description) >= 30, (
                f"{target.name}: description too short ({len(target.description)} chars)"
            )


class TestAllFieldsPopulated:
    """Every target must have all required fields populated."""

    def test_target_fields_populated(self, manifest):
        for target in manifest.targets:
            assert target.name
            assert target.url
            assert target.url.startswith("https://")
            assert target.ref
            assert target.include
            assert target.description

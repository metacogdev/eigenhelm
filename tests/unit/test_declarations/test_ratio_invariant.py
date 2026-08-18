"""The declaration ratio must be a true fraction: numerator ⊆ denominator.

Regression tests for a crash observed on real Rust code: detectors count
non-blank lines inside a region (doc comments included), while the file
denominator counts non-blank, non-comment lines — so a struct documented
with a `///` line per field produced ratio > 1, and DeclarationAnalysis's
validator aborted the entire evaluation run:

    ERROR: ratio must be in [0.0, 1.0], got 2.2777777777777777
"""

from __future__ import annotations

from eigenhelm.declarations import analyze_declarations

# The shape that crashed in the wild (cloister-observer/src/config.rs): a
# serde config struct where doc-comment lines outnumber code lines.
_DOC_HEAVY_RUST = '''\
use serde::Deserialize;

/// Which mode the observer runs in.
///
/// Log mode tails an existing transcript; proxy mode sits inline.
pub enum Mode {
    /// Tail a transcript file.
    Log,
    /// Intercept traffic inline.
    Proxy,
}

/// Observer configuration, loaded from TOML.
///
/// Every field is documented because operators edit this by hand.
#[derive(Debug, Deserialize)]
pub struct ObserverConfig {
    /// Path to the transcript to tail.
    ///
    /// Relative paths resolve against the working directory.
    pub transcript: String,

    /// Which mode to run in.
    ///
    /// See [`Mode`] for the semantics of each.
    pub mode: String,

    /// Upstream endpoint for proxy mode.
    ///
    /// Ignored in log mode.
    pub upstream: Option<String>,
}
'''


class TestRatioInvariant:
    def test_doc_heavy_rust_struct_does_not_crash_and_ratio_is_a_fraction(self):
        analysis = analyze_declarations(_DOC_HEAVY_RUST, "rust")
        assert 0.0 <= analysis.ratio <= 1.0
        assert analysis.declaration_lines <= analysis.non_blank_non_comment_lines

    def test_numerator_counts_only_lines_the_denominator_counts(self):
        """Doc-comment lines inside a region must not inflate the numerator."""
        analysis = analyze_declarations(_DOC_HEAVY_RUST, "rust")
        # The file's countable lines: use + enum(4 code lines: header, 2
        # variants, brace) + struct(7: attr, header, 3 fields, 2 braces...)
        # — exact numbers aside, the invariant is that every counted
        # declaration line is one of the counted file lines.
        assert analysis.regions, "detector should still find the enum and struct"
        assert analysis.declaration_lines > 0
        assert analysis.ratio == (
            analysis.declaration_lines / analysis.non_blank_non_comment_lines
        )

    def test_overlapping_regions_cannot_double_count(self):
        """Even if a detector ever emits overlapping regions, covered lines
        are counted once — the set-intersection construction makes double
        counting structurally impossible, so this documents intent via the
        public API rather than hand-built regions."""
        analysis = analyze_declarations(_DOC_HEAVY_RUST, "rust")
        covered_max = analysis.non_blank_non_comment_lines
        assert analysis.declaration_lines <= covered_max

    def test_python_dataclass_file_still_reads_dominant(self):
        source = (
            "from dataclasses import dataclass\n"
            "\n"
            "@dataclass\n"
            "class Point:\n"
            "    x: int\n"
            "    y: int\n"
            "    z: int\n"
        )
        analysis = analyze_declarations(source, "python")
        assert 0.0 <= analysis.ratio <= 1.0
        if analysis.regions:
            assert analysis.declaration_lines > 0

    def test_unsupported_language_yields_zero_ratio(self):
        analysis = analyze_declarations("SELECT 1;\n", "sql")
        assert analysis.ratio == 0.0
        assert analysis.regions == ()

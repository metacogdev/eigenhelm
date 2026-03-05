"""VirtueExtractor: concrete implementation of IVirtueExtractor.

Orchestrates Tree-sitter parsing, Halstead, Cyclomatic, and WL hash metrics
into a 69-dimensional feature vector, and optionally projects into PCA eigenspace.
"""

from __future__ import annotations

import numpy as np

from eigenhelm.metrics import cyclomatic as cyclomatic_mod
from eigenhelm.metrics import halstead as halstead_mod
from eigenhelm.metrics import wl_hash as wl_mod
from eigenhelm.models import (
    FEATURE_DIM,
    WL_BINS,
    CodeUnit,
    EigenspaceModel,
    FeatureVector,
    HalsteadMetrics,
    ProjectionResult,
    UnsupportedLanguageError,
)
from eigenhelm.parsers import language_map
from eigenhelm.parsers import tree_sitter as ts_parser


class VirtueExtractor:
    """Stage 1 IVirtueExtractor implementation.

    Stateless — safe to share across threads for read-only use.
    (PCA projection reads model immutably.)
    """

    def __init__(self, wl_iterations: int = 3) -> None:
        """
        Args:
            wl_iterations: WL graph hash refinement depth (1–5, default 3).
        """
        self._wl_iterations = max(1, min(wl_iterations, 5))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract(
        self, source: str, language: str, file_path: str | None = None
    ) -> list[FeatureVector]:
        """Extract 69-dim feature vectors from source code.

        Splits source into code units (functions/classes) and computes
        Halstead + Cyclomatic + WL hash metrics for each.

        Args:
            source: Raw source code string.
            language: Language identifier (e.g., "python", "rust").
            file_path: Optional source file path for annotation.

        Returns:
            List of FeatureVector, one per code unit found.

        Raises:
            UnsupportedLanguageError: If no grammar for the language.
        """
        if not source.strip():
            return []

        if not language_map.is_supported(language):
            raise UnsupportedLanguageError(language)

        units, partial = ts_parser.extract_units_partial(source, language, file_path)

        warning = None
        if partial:
            warning = "Partial AST: source contained syntax errors"

        vectors = []
        for unit in units:
            fv = self._extract_unit(unit, partial_parse=partial, warning=warning)
            vectors.append(fv)
        return vectors

    def extract_batch(
        self,
        files: list[tuple[str, str, str]],
    ) -> list[FeatureVector]:
        """Extract feature vectors from multiple files sequentially.

        Args:
            files: List of (source, language, file_path) tuples.

        Returns:
            Flat list of FeatureVector across all files.
            Unsupported languages produce a zero vector with warning;
            they do NOT halt the batch.
        """
        results: list[FeatureVector] = []
        for source, language, file_path in files:
            if not language_map.is_supported(language):
                # Return a sentinel zero vector rather than raising.
                dummy_unit = CodeUnit(
                    source=source,
                    language=language,
                    name="<unsupported>",
                    start_line=1,
                    end_line=1,
                    file_path=file_path,
                )
                results.append(
                    FeatureVector(
                        values=np.zeros(FEATURE_DIM, dtype=np.float64),
                        code_unit=dummy_unit,
                        partial_parse=True,
                        warning=f"Unsupported language: {language!r}",
                    )
                )
                continue

            try:
                vectors = self.extract(source, language, file_path)
                results.extend(vectors)
            except Exception as exc:  # noqa: BLE001
                dummy_unit = CodeUnit(
                    source=source[:200],
                    language=language,
                    name="<error>",
                    start_line=1,
                    end_line=1,
                    file_path=file_path,
                )
                results.append(
                    FeatureVector(
                        values=np.zeros(FEATURE_DIM, dtype=np.float64),
                        code_unit=dummy_unit,
                        partial_parse=True,
                        warning=str(exc),
                    )
                )

        return results

    def project(
        self,
        vector: FeatureVector,
        model: EigenspaceModel,
    ) -> ProjectionResult:
        """Project a FeatureVector into the PCA eigenspace.

        z = (x - μ) / σ @ W
        L_drift  = ||x_reconstructed - x_normalized||₂
        L_virtue = ||z||₂  (distance from origin = elite centroid)

        Args:
            vector: FeatureVector from extract().
            model: Loaded EigenspaceModel.

        Returns:
            ProjectionResult with coordinates, L_drift, L_virtue, quality_flag.

        Raises:
            RuntimeError: If model is None.
        """
        if model is None:
            raise RuntimeError(
                "VirtueExtractor.project() requires a loaded EigenspaceModel. "
                "Call eigenhelm.eigenspace.load_model() first."
            )
        from eigenhelm.eigenspace.projection import project as _project

        return _project(vector, model)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _extract_unit(
        self,
        unit: CodeUnit,
        partial_parse: bool = False,
        warning: str | None = None,
    ) -> FeatureVector:
        """Compute all metrics for one CodeUnit and assemble the feature vector."""
        # Parse the unit's own source for metric extraction.
        ast_root = ts_parser.parse_source(unit.source, unit.language)

        # --- Halstead ---
        if ast_root is not None:
            h_metrics = halstead_mod.compute(ast_root)
        else:
            h_metrics = HalsteadMetrics(
                volume=0.0,
                difficulty=0.0,
                effort=0.0,
                distinct_operators=0,
                distinct_operands=0,
                total_operators=0,
                total_operands=0,
            )

        # --- Cyclomatic ---
        c_metrics = cyclomatic_mod.compute(unit.source, unit.language, name=unit.name)

        # --- WL hash ---
        if ast_root is not None:
            wl_hist = wl_mod.compute(ast_root, iterations=self._wl_iterations)
        else:
            wl_hist = np.zeros(WL_BINS, dtype=np.float64)

        # --- Token count warning ---
        if wl_hist.sum() == 0 and not warning:
            warning = "Zero-token input; WL histogram is zero"
        elif c_metrics.nloc < 20 and not partial_parse:
            # Low NLOC; Halstead and cyclomatic density may be unreliable
            # for very small snippets (below meaningful measurement threshold).
            if not warning:
                warning = "Low token count (<20 LoC); metrics may be unreliable"

        # --- Assemble 69-dim vector ---
        values = np.empty(FEATURE_DIM, dtype=np.float64)
        values[0] = h_metrics.volume
        values[1] = h_metrics.difficulty
        values[2] = h_metrics.effort
        values[3] = float(c_metrics.complexity)
        values[4] = c_metrics.density
        values[5:] = wl_hist

        return FeatureVector(
            values=values,
            code_unit=unit,
            partial_parse=partial_parse,
            warning=warning,
        )

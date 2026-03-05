"""Core data structures for the IVirtueExtractor pipeline.

Feature vector schema (69 dimensions, float64):
  [0]   Halstead Volume (V)
  [1]   Halstead Difficulty (D)
  [2]   Halstead Effort (E)
  [3]   Cyclomatic Complexity v(G)
  [4]   Cyclomatic Density (v(G) / nloc)
  [5-68] WL graph hash histogram (64 bins, normalized to sum=1)
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# Stable feature vector dimension for alpha.
FEATURE_DIM = 69
WL_BINS = 64
SCALAR_METRICS = 5  # V, D, E, v(G), density


@dataclass(frozen=True)
class CodeUnit:
    """A single extractable unit of source code (function, method, or class)."""

    source: str
    language: str
    name: str
    start_line: int
    end_line: int
    file_path: str | None = None


@dataclass(frozen=True)
class HalsteadMetrics:
    """Halstead complexity measures from AST-structural node classification.

    Reference: Halstead, M.H. (1977). Elements of Software Science.
    Classification: branch/control-flow/call/assignment/return → operators;
                    leaf identifier/literal → operands.
    """

    volume: float  # V = N * log2(η)
    difficulty: float  # D = (η₁/2) * (N₂/η₂)
    effort: float  # E = D * V
    distinct_operators: int  # η₁
    distinct_operands: int  # η₂
    total_operators: int  # N₁
    total_operands: int  # N₂


@dataclass(frozen=True)
class CyclomaticMetrics:
    """Cyclomatic complexity via Lizard, normalized to density.

    Reference: McCabe, T.J. (1976). A complexity measure.
    """

    complexity: int  # v(G)
    nloc: int  # non-comment lines of code
    density: float  # v(G) / nloc


@dataclass(frozen=True)
class FeatureVector:
    """69-dimensional numeric feature vector for one CodeUnit.

    values[0:5]  — scalar metrics: V, D, E, v(G), density
    values[5:69] — WL hash histogram (64 bins, sum ≈ 1.0)
    """

    values: np.ndarray  # shape (69,), dtype float64
    code_unit: CodeUnit
    partial_parse: bool = False
    warning: str | None = None

    def __post_init__(self) -> None:
        if self.values.shape != (FEATURE_DIM,):
            raise ValueError(
                f"FeatureVector.values must be shape ({FEATURE_DIM},), got {self.values.shape}"
            )
        if self.values.dtype != np.float64:
            object.__setattr__(self, "values", self.values.astype(np.float64))


@dataclass(frozen=True)
class CalibrationStats:
    """Calibration statistics derived from the training corpus.

    Produced by compute_calibration() in training/pca.py and carried
    by TrainingResult for reporting and model serialization.

    sigma_drift and sigma_virtue are the p-th percentile of l_drift and
    l_virtue observed across all training projections (Jolliffe 2002,
    Chapter 2). They normalize manifold dimensions in AestheticCritic so
    that in-corpus code does not saturate at the penalty cap.
    """

    sigma_drift: float
    sigma_virtue: float
    n_projections: int
    percentile: float = 95.0

    def __post_init__(self) -> None:
        if self.sigma_drift <= 0:
            raise ValueError(f"CalibrationStats.sigma_drift must be > 0, got {self.sigma_drift}")
        if self.sigma_virtue <= 0:
            raise ValueError(f"CalibrationStats.sigma_virtue must be > 0, got {self.sigma_virtue}")
        if self.n_projections <= 0:
            raise ValueError(
                f"CalibrationStats.n_projections must be > 0, got {self.n_projections}"
            )
        if not (0.0 < self.percentile <= 100.0):
            raise ValueError(
                f"CalibrationStats.percentile must be in (0, 100], got {self.percentile}"
            )


@dataclass(frozen=True)
class EigenspaceModel:
    """Pre-computed PCA model for eigenspace projection.

    Serialized as .npz: keys projection_matrix, mean, std,
    n_components, version, corpus_hash, sigma_drift, sigma_virtue.
    """

    projection_matrix: np.ndarray  # shape (69, k)
    mean: np.ndarray  # shape (69,)
    std: np.ndarray  # shape (69,)
    n_components: int
    version: str
    corpus_hash: str
    sigma_drift: float = 1.0  # p95 l_drift from training corpus; 1.0 = pre-calibration default
    sigma_virtue: float = 1.0  # p95 l_virtue from training corpus; 1.0 = pre-calibration default

    def __post_init__(self) -> None:
        if self.projection_matrix.shape[0] != FEATURE_DIM:
            raise ValueError(
                f"projection_matrix.shape[0] must be {FEATURE_DIM}, "
                f"got {self.projection_matrix.shape[0]}"
            )
        if np.any(self.std <= 0):
            raise ValueError("EigenspaceModel.std must be > 0 for all dimensions")
        if self.sigma_drift <= 0:
            raise ValueError(f"EigenspaceModel.sigma_drift must be > 0, got {self.sigma_drift}")
        if self.sigma_virtue <= 0:
            raise ValueError(f"EigenspaceModel.sigma_virtue must be > 0, got {self.sigma_virtue}")


@dataclass(frozen=True)
class ProjectionResult:
    """Output of PCA eigenspace projection.

    quality_flag values:
      "nominal"       — normal projection
      "partial_input" — source FeatureVector had partial_parse=True
      "high_drift"    — L_drift > 2σ (likely out-of-distribution)
    """

    coordinates: np.ndarray  # shape (k,)
    l_drift: float
    l_virtue: float
    quality_flag: str


@dataclass(frozen=True)
class TrainingResult:
    """Output of the PCA eigenspace training pipeline.

    Encapsulates the trained model plus metadata needed for the training report.
    Deterministic — identical corpus produces identical result.
    """

    model: EigenspaceModel
    explained_variance_ratio: np.ndarray  # shape (k,), dtype float64
    cumulative_variance: float
    n_files_processed: int
    n_files_skipped: int
    n_units_extracted: int
    n_vectors_excluded: int
    calibration: CalibrationStats | None = None


class UnsupportedLanguageError(Exception):
    """Raised when no Tree-sitter grammar is available for a language."""

    def __init__(self, language: str) -> None:
        self.language = language
        super().__init__(f"No grammar available for language: {language!r}")

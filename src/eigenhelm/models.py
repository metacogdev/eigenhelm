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
            raise ValueError(
                f"CalibrationStats.sigma_drift must be > 0, got {self.sigma_drift}"
            )
        if self.sigma_virtue <= 0:
            raise ValueError(
                f"CalibrationStats.sigma_virtue must be > 0, got {self.sigma_virtue}"
            )
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
    sigma_drift: float = (
        1.0  # p95 l_drift from training corpus; 1.0 = pre-calibration default
    )
    sigma_virtue: float = (
        1.0  # p95 l_virtue from training corpus; 1.0 = pre-calibration default
    )
    exemplars: list[ExemplarRef] | None = None  # None = pre-010 model
    n_exemplars: int = 0  # Informational; len(exemplars) when set
    language: str | None = None  # Training language key; None = pre-009 model
    corpus_class: str | None = (
        None  # "A" (single-lang), "B" (cross-lang); None = pre-009
    )
    n_training_files: int = 0  # Files processed during training; 0 = pre-009
    calibrated_accept: float | None = None  # p25 score threshold; None = pre-015 model
    calibrated_reject: float | None = None  # p75 score threshold; None = pre-015 model
    score_distribution: ScoreDistribution | None = (
        None  # Full distribution; None = pre-015
    )

    def __post_init__(self) -> None:
        if self.projection_matrix.shape[0] != FEATURE_DIM:
            raise ValueError(
                f"projection_matrix.shape[0] must be {FEATURE_DIM}, "
                f"got {self.projection_matrix.shape[0]}"
            )
        if np.any(self.std <= 0):
            raise ValueError("EigenspaceModel.std must be > 0 for all dimensions")
        if self.sigma_drift <= 0:
            raise ValueError(
                f"EigenspaceModel.sigma_drift must be > 0, got {self.sigma_drift}"
            )
        if self.sigma_virtue <= 0:
            raise ValueError(
                f"EigenspaceModel.sigma_virtue must be > 0, got {self.sigma_virtue}"
            )


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
    x_norm: np.ndarray | None = (
        None  # shape (69,) — standardized input (for attribution)
    )
    x_rec: np.ndarray | None = (
        None  # shape (69,) — PCA reconstruction (for attribution)
    )


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
    exemplars: list[ExemplarRef] | None = (
        None  # Populated when exemplar selection succeeds
    )
    score_distribution: ScoreDistribution | None = (
        None  # 015: training score distribution
    )
    calibration_skip_reason: str | None = (
        None  # 015: why threshold calibration was skipped
    )


@dataclass(frozen=True)
class ExemplarRef:
    """A representative code sample selected from the training corpus.

    Stores compressed content for NCD computation at evaluation time,
    avoiding dependency on the original training corpus.
    """

    index: int  # Row index in the original design matrix
    cluster: int  # PCA cluster membership (0-indexed)
    compressed_content: bytes  # zlib.compress(source_bytes, level=9)
    content_hash: str  # SHA-256 of original source_bytes
    file_path: str | None = None  # Originating file path (informational)


@dataclass(frozen=True)
class MetricThresholds:
    """Configurable target thresholds from the corpus research report.

    Default values from corpus research: Birkhoff > 0.8, CD < 0.1,
    WL consistency > 0.9. Overridable at evaluation time (FR-007).
    """

    birkhoff_min: float = 0.8
    cyclomatic_density_max: float = 0.1
    wl_consistency_min: float = 0.9


@dataclass(frozen=True)
class ScoreDistribution:
    """Summary statistics of aesthetic scores computed over a training corpus.

    All values are in [0.0, 1.0] and monotonically non-decreasing.
    Produced during training by compute_score_distribution() in training/calibration.py.
    """

    min: float
    p10: float
    p25: float
    median: float
    p75: float
    p90: float
    max: float
    n_scores: int

    def __post_init__(self) -> None:
        values = [
            self.min,
            self.p10,
            self.p25,
            self.median,
            self.p75,
            self.p90,
            self.max,
        ]
        for i, v in enumerate(values):
            if not (0.0 <= v <= 1.0):
                names = ["min", "p10", "p25", "median", "p75", "p90", "max"]
                raise ValueError(
                    f"ScoreDistribution.{names[i]} must be in [0.0, 1.0], got {v}"
                )
        for i in range(len(values) - 1):
            if values[i] > values[i + 1]:
                names = ["min", "p10", "p25", "median", "p75", "p90", "max"]
                raise ValueError(
                    f"ScoreDistribution values must be monotonically non-decreasing: "
                    f"{names[i]}={values[i]} > {names[i + 1]}={values[i + 1]}"
                )
        if self.n_scores < 1:
            raise ValueError(
                f"ScoreDistribution.n_scores must be >= 1, got {self.n_scores}"
            )


@dataclass(frozen=True)
class CalibrationThresholds:
    """Accept and reject thresholds derived from a training score distribution.

    accept: scores below this are classified "accept"
    reject: scores above this are classified "reject"
    source_percentiles: (p_accept, p_reject) used to derive the thresholds
    n_scores: number of scores used in calibration
    """

    accept: float
    reject: float
    source_percentiles: tuple[float, float]
    n_scores: int

    def __post_init__(self) -> None:
        if not (0.0 <= self.accept <= 1.0):
            raise ValueError(
                f"CalibrationThresholds.accept must be in [0.0, 1.0], got {self.accept}"
            )
        if not (0.0 <= self.reject <= 1.0):
            raise ValueError(
                f"CalibrationThresholds.reject must be in [0.0, 1.0], got {self.reject}"
            )
        if self.accept >= self.reject:
            raise ValueError(
                f"CalibrationThresholds.accept ({self.accept}) must be < "
                f"reject ({self.reject})"
            )


class UnsupportedLanguageError(Exception):
    """Raised when no Tree-sitter grammar is available for a language."""

    def __init__(self, language: str) -> None:
        self.language = language
        super().__init__(f"No grammar available for language: {language!r}")

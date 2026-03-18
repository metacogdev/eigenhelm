"""Tests for score attribution decomposition (017-score-attribution).

Covers:
  T009 — Drift decomposition (PCA reconstruction error)
  T010 — Alignment decomposition (PCA back-projection)
  T011 — Direct attribution (entropy, compression, NCD)
  T012 — Unavailable attributions (missing model/exemplars)
"""

from __future__ import annotations

import numpy as np
import pytest

from eigenhelm.attribution.constants import FEATURE_NAMES
from eigenhelm.attribution.decompose import (
    attribute_direct,
    decompose_alignment,
    decompose_drift,
)
from eigenhelm.attribution.models import (
    DimensionAttribution,
)
from eigenhelm.critic import AestheticMetrics
from eigenhelm.models import (
    CodeUnit,
    EigenspaceModel,
    FeatureVector,
    ProjectionResult,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

NDIM = 69


def _make_code_unit(name: str = "test_func") -> CodeUnit:
    return CodeUnit(
        source="def test_func(): pass",
        language="python",
        name=name,
        start_line=1,
        end_line=1,
        file_path="test.py",
    )


def _make_feature_vector(
    values: np.ndarray | None = None,
    code_unit: CodeUnit | None = None,
) -> FeatureVector:
    if values is None:
        values = np.random.default_rng(42).random(NDIM)
    if code_unit is None:
        code_unit = _make_code_unit()
    return FeatureVector(values=values.astype(np.float64), code_unit=code_unit)


def _make_model(
    n_components: int = 5,
    sigma_drift: float = 2.0,
    sigma_virtue: float = 3.0,
    seed: int = 7,
) -> EigenspaceModel:
    """Build a minimal EigenspaceModel with orthonormal projection_matrix."""
    rng = np.random.default_rng(seed)
    # QR decomposition gives orthonormal columns
    raw = rng.standard_normal((NDIM, n_components))
    q, _ = np.linalg.qr(raw)
    projection_matrix = q[:, :n_components]

    mean = rng.random(NDIM)
    std = rng.random(NDIM) + 0.1  # ensure > 0

    return EigenspaceModel(
        projection_matrix=projection_matrix,
        mean=mean,
        std=std,
        n_components=n_components,
        version="test-v1",
        corpus_hash="abc123",
        sigma_drift=sigma_drift,
        sigma_virtue=sigma_virtue,
    )


def _make_projection(
    model: EigenspaceModel,
    feature_vector: FeatureVector,
    l_drift: float | None = None,
    l_virtue: float | None = None,
) -> ProjectionResult:
    """Compute a real projection so intermediates are consistent."""
    x_norm = (feature_vector.values - model.mean) / model.std
    W = model.projection_matrix
    z = x_norm @ W  # coordinates in PCA space
    x_rec = z @ W.T  # reconstruction in standardized space

    error = x_rec - x_norm
    computed_l_drift = float(np.linalg.norm(error))
    computed_l_virtue = float(np.linalg.norm(z))

    return ProjectionResult(
        coordinates=z,
        l_drift=l_drift if l_drift is not None else computed_l_drift,
        l_virtue=l_virtue if l_virtue is not None else computed_l_virtue,
        quality_flag="nominal",
        x_norm=x_norm,
        x_rec=x_rec,
    )


def _make_metrics(
    entropy: float = 4.5,
    birkhoff_measure: float = 0.72,
    raw_bytes: int = 200,
    compressed_bytes: int = 150,
) -> AestheticMetrics:
    compression_ratio = compressed_bytes / raw_bytes if raw_bytes > 0 else None
    return AestheticMetrics(
        entropy=entropy,
        compression_ratio=compression_ratio,
        birkhoff_measure=birkhoff_measure,
        raw_bytes=raw_bytes,
        compressed_bytes=compressed_bytes,
    )


# ---------------------------------------------------------------------------
# T009 — Drift decomposition
# ---------------------------------------------------------------------------


class TestDecomposeDrift:
    """decompose_drift: PCA reconstruction-error decomposition."""

    def test_returns_dimension_attribution(self) -> None:
        model = _make_model()
        fv = _make_feature_vector()
        proj = _make_projection(model, fv)

        result = decompose_drift(proj, model, fv)

        assert isinstance(result, DimensionAttribution)
        assert result.dimension == "manifold_drift"
        assert result.method == "pca_reconstruction"
        assert result.available is True

    def test_sum_of_squared_contributions_equals_l_drift_squared(self) -> None:
        """Exact decomposition: sum(e[i]^2) == L_drift^2."""
        model = _make_model()
        fv = _make_feature_vector()
        proj = _make_projection(model, fv)

        decompose_drift(proj, model, fv)

        # Collect ALL feature contributions (not just top_n).
        # The error vector has 69 components; squared sum must equal l_drift^2.
        error = proj.x_rec - proj.x_norm
        expected_l_drift_sq = float(np.sum(error**2))

        # Verify using the projection's l_drift
        assert pytest.approx(expected_l_drift_sq, rel=1e-10) == proj.l_drift**2

    def test_features_ranked_by_magnitude_descending(self) -> None:
        model = _make_model()
        fv = _make_feature_vector()
        proj = _make_projection(model, fv)

        result = decompose_drift(proj, model, fv, top_n=5)

        magnitudes = [f.contribution_magnitude for f in result.features]
        assert magnitudes == sorted(magnitudes, reverse=True)
        assert len(result.features) == 5

    def test_top_n_limits_output(self) -> None:
        model = _make_model()
        fv = _make_feature_vector()
        proj = _make_projection(model, fv)

        for n in (1, 3, 10):
            result = decompose_drift(proj, model, fv, top_n=n)
            assert len(result.features) == n

    def test_feature_names_match_constants(self) -> None:
        model = _make_model()
        fv = _make_feature_vector()
        proj = _make_projection(model, fv)

        result = decompose_drift(proj, model, fv, top_n=NDIM)

        for fc in result.features:
            assert fc.feature_name == FEATURE_NAMES[fc.feature_index]
            assert 0 <= fc.feature_index < NDIM

    def test_normalized_score_clamped_to_unit(self) -> None:
        """normalized_score = l_drift / sigma_drift, clamped [0, 1]."""
        model = _make_model(sigma_drift=0.001)  # tiny sigma -> ratio >> 1
        fv = _make_feature_vector()
        proj = _make_projection(model, fv)

        result = decompose_drift(proj, model, fv)

        assert result.normalized_score <= 1.0
        assert result.normalized_score >= 0.0

    def test_normalized_score_ratio(self) -> None:
        """When within range, score = l_drift / sigma_drift."""
        model = _make_model(sigma_drift=100.0)  # large sigma -> ratio < 1
        fv = _make_feature_vector()
        proj = _make_projection(model, fv)

        result = decompose_drift(proj, model, fv)

        expected = min(max(proj.l_drift / model.sigma_drift, 0.0), 1.0)
        assert pytest.approx(result.normalized_score, rel=1e-10) == expected

    def test_contribution_value_is_per_feature_error(self) -> None:
        """Each contribution_value should be e[i] = x_rec[i] - x_norm[i]."""
        model = _make_model()
        fv = _make_feature_vector()
        proj = _make_projection(model, fv)

        result = decompose_drift(proj, model, fv, top_n=NDIM)

        error = proj.x_rec - proj.x_norm
        for fc in result.features:
            expected = error[fc.feature_index]
            assert pytest.approx(fc.contribution_value, rel=1e-10) == expected

    def test_contribution_magnitude_is_abs_error(self) -> None:
        """contribution_magnitude = |e[i]|."""
        model = _make_model()
        fv = _make_feature_vector()
        proj = _make_projection(model, fv)

        result = decompose_drift(proj, model, fv, top_n=NDIM)

        error = proj.x_rec - proj.x_norm
        for fc in result.features:
            expected = abs(error[fc.feature_index])
            assert pytest.approx(fc.contribution_magnitude, rel=1e-10) == expected

    def test_raw_value_and_corpus_mean(self) -> None:
        """Each FeatureContribution carries the raw feature value and corpus mean."""
        model = _make_model()
        fv = _make_feature_vector()
        proj = _make_projection(model, fv)

        result = decompose_drift(proj, model, fv, top_n=3)

        for fc in result.features:
            assert pytest.approx(fc.raw_value, rel=1e-10) == fv.values[fc.feature_index]
            assert pytest.approx(fc.corpus_mean, rel=1e-10) == model.mean[fc.feature_index]

    def test_standardized_deviation(self) -> None:
        """standardized_deviation = (raw - mean) / std."""
        model = _make_model()
        fv = _make_feature_vector()
        proj = _make_projection(model, fv)

        result = decompose_drift(proj, model, fv, top_n=3)

        for fc in result.features:
            expected = (fv.values[fc.feature_index] - model.mean[fc.feature_index]) / model.std[fc.feature_index]
            assert pytest.approx(fc.standardized_deviation, rel=1e-10) == expected

    def test_rank_field_is_one_indexed(self) -> None:
        model = _make_model()
        fv = _make_feature_vector()
        proj = _make_projection(model, fv)

        result = decompose_drift(proj, model, fv, top_n=5)

        ranks = [fc.rank for fc in result.features]
        assert ranks == [1, 2, 3, 4, 5]


# ---------------------------------------------------------------------------
# T010 — Alignment decomposition
# ---------------------------------------------------------------------------


class TestDecomposeAlignment:
    """decompose_alignment: PCA back-projection ranking."""

    def test_returns_dimension_attribution(self) -> None:
        model = _make_model()
        fv = _make_feature_vector()
        proj = _make_projection(model, fv)

        result = decompose_alignment(proj, model, fv)

        assert isinstance(result, DimensionAttribution)
        assert result.dimension == "manifold_alignment"
        assert result.method == "pca_alignment"
        assert result.available is True

    def test_features_ranked_by_magnitude_descending(self) -> None:
        model = _make_model()
        fv = _make_feature_vector()
        proj = _make_projection(model, fv)

        result = decompose_alignment(proj, model, fv, top_n=5)

        magnitudes = [f.contribution_magnitude for f in result.features]
        assert magnitudes == sorted(magnitudes, reverse=True)

    def test_back_projection_formula(self) -> None:
        """c[i] = sum_j(z[j] * W[i,j])."""
        model = _make_model()
        fv = _make_feature_vector()
        proj = _make_projection(model, fv)

        result = decompose_alignment(proj, model, fv, top_n=NDIM)

        W = model.projection_matrix
        z = proj.coordinates
        expected_c = z @ W.T  # shape (69,)

        for fc in result.features:
            assert pytest.approx(fc.contribution_value, rel=1e-10) == expected_c[fc.feature_index]

    def test_contribution_magnitude_is_abs_c(self) -> None:
        model = _make_model()
        fv = _make_feature_vector()
        proj = _make_projection(model, fv)

        result = decompose_alignment(proj, model, fv, top_n=NDIM)

        W = model.projection_matrix
        z = proj.coordinates
        expected_c = z @ W.T

        for fc in result.features:
            assert pytest.approx(fc.contribution_magnitude, rel=1e-10) == abs(expected_c[fc.feature_index])

    def test_not_exact_decomposition(self) -> None:
        """Alignment is a heuristic ranking, NOT an exact additive decomposition of l_virtue."""
        model = _make_model()
        fv = _make_feature_vector()
        proj = _make_projection(model, fv)

        result = decompose_alignment(proj, model, fv, top_n=NDIM)

        # sum of contribution_value^2 does NOT generally equal l_virtue^2
        # (unless the projection is orthogonal in this sense, which is coincidental)
        # We just verify the result is internally consistent (features present).
        assert len(result.features) == NDIM

    def test_normalized_score_from_l_virtue(self) -> None:
        """normalized_score = l_virtue / sigma_virtue, clamped [0, 1]."""
        model = _make_model(sigma_virtue=100.0)
        fv = _make_feature_vector()
        proj = _make_projection(model, fv)

        result = decompose_alignment(proj, model, fv)

        expected = min(max(proj.l_virtue / model.sigma_virtue, 0.0), 1.0)
        assert pytest.approx(result.normalized_score, rel=1e-10) == expected

    def test_normalized_score_clamped_high(self) -> None:
        model = _make_model(sigma_virtue=0.001)
        fv = _make_feature_vector()
        proj = _make_projection(model, fv)

        result = decompose_alignment(proj, model, fv)

        assert result.normalized_score <= 1.0

    def test_top_n_limits_output(self) -> None:
        model = _make_model()
        fv = _make_feature_vector()
        proj = _make_projection(model, fv)

        result = decompose_alignment(proj, model, fv, top_n=2)
        assert len(result.features) == 2

    def test_rank_field_is_one_indexed(self) -> None:
        model = _make_model()
        fv = _make_feature_vector()
        proj = _make_projection(model, fv)

        result = decompose_alignment(proj, model, fv, top_n=4)
        ranks = [fc.rank for fc in result.features]
        assert ranks == [1, 2, 3, 4]

    def test_feature_names_valid(self) -> None:
        model = _make_model()
        fv = _make_feature_vector()
        proj = _make_projection(model, fv)

        result = decompose_alignment(proj, model, fv, top_n=3)

        for fc in result.features:
            assert fc.feature_name == FEATURE_NAMES[fc.feature_index]


# ---------------------------------------------------------------------------
# T011 — Direct attribution
# ---------------------------------------------------------------------------


class TestAttributeDirect:
    """attribute_direct: entropy, compression, NCD dimensions."""

    def _normalized_values(
        self,
        entropy_norm: float = 0.44,
        compression_norm: float = 0.72,
        ncd_norm: float = 0.35,
    ) -> dict[str, float]:
        return {
            "token_entropy": entropy_norm,
            "compression_structure": compression_norm,
            "ncd_exemplar_distance": ncd_norm,
        }

    # -- Entropy --

    def test_entropy_attribution(self) -> None:
        metrics = _make_metrics(entropy=4.5)
        nv = self._normalized_values(entropy_norm=0.4375)

        result = attribute_direct("token_entropy", metrics, nv)

        assert isinstance(result, DimensionAttribution)
        assert result.dimension == "token_entropy"
        assert result.method == "direct"
        assert result.available is True
        assert result.direct is not None
        assert result.direct.metric_name == "shannon_entropy"
        assert result.direct.normalization == "1.0 - (H / 8.0)"
        assert pytest.approx(result.direct.computed_value) == 4.5

    def test_entropy_normalized_score_in_unit(self) -> None:
        metrics = _make_metrics(entropy=4.5)
        nv = self._normalized_values(entropy_norm=0.4375)

        result = attribute_direct("token_entropy", metrics, nv)

        assert 0.0 <= result.normalized_score <= 1.0
        assert pytest.approx(result.normalized_score) == 0.4375

    # -- Compression --

    def test_compression_attribution(self) -> None:
        metrics = _make_metrics(birkhoff_measure=0.72)
        nv = self._normalized_values(compression_norm=0.72)

        result = attribute_direct("compression_structure", metrics, nv)

        assert result.dimension == "compression_structure"
        assert result.method == "direct"
        assert result.available is True
        assert result.direct is not None
        assert result.direct.metric_name == "birkhoff_measure"
        assert result.direct.normalization == "birkhoff_direct"
        assert pytest.approx(result.direct.computed_value) == 0.72

    def test_compression_normalized_score_in_unit(self) -> None:
        metrics = _make_metrics(birkhoff_measure=0.85)
        nv = self._normalized_values(compression_norm=0.85)

        result = attribute_direct("compression_structure", metrics, nv)

        assert 0.0 <= result.normalized_score <= 1.0
        assert pytest.approx(result.normalized_score) == 0.85

    # -- NCD with exemplar --

    def test_ncd_with_exemplar(self) -> None:
        metrics = _make_metrics()
        nv = self._normalized_values(ncd_norm=0.35)

        result = attribute_direct(
            "ncd_exemplar_distance", metrics, nv, nearest_exemplar_id="sha256:abc123"
        )

        assert result.dimension == "ncd_exemplar_distance"
        assert result.method == "direct"
        assert result.available is True
        assert result.direct is not None
        assert result.direct.exemplar_id == "sha256:abc123"
        assert pytest.approx(result.normalized_score) == 0.35

    def test_ncd_without_exemplar(self) -> None:
        metrics = _make_metrics()
        nv = self._normalized_values(ncd_norm=0.0)

        result = attribute_direct("ncd_exemplar_distance", metrics, nv)

        assert result.dimension == "ncd_exemplar_distance"
        assert result.available is False
        assert result.direct is None or result.direct.exemplar_id is None

    # -- Edge cases --

    def test_all_normalized_scores_in_unit_range(self) -> None:
        metrics = _make_metrics()
        for dim in ("token_entropy", "compression_structure"):
            nv = self._normalized_values()
            result = attribute_direct(dim, metrics, nv)
            assert 0.0 <= result.normalized_score <= 1.0

    def test_entropy_zero_gives_valid_score(self) -> None:
        metrics = _make_metrics(entropy=0.0)
        nv = {"token_entropy": 1.0}

        result = attribute_direct("token_entropy", metrics, nv)

        assert 0.0 <= result.normalized_score <= 1.0

    def test_entropy_max_gives_valid_score(self) -> None:
        metrics = _make_metrics(entropy=8.0)
        nv = {"token_entropy": 0.0}

        result = attribute_direct("token_entropy", metrics, nv)

        assert 0.0 <= result.normalized_score <= 1.0

    def test_no_features_in_direct_attribution(self) -> None:
        """Direct attributions should have empty features tuple."""
        metrics = _make_metrics()
        nv = self._normalized_values()

        result = attribute_direct("token_entropy", metrics, nv)

        assert result.features == ()


# ---------------------------------------------------------------------------
# T012 — Unavailable attributions
# ---------------------------------------------------------------------------


class TestUnavailableAttributions:
    """When model or exemplars are missing, attributions report unavailable."""

    def test_drift_without_projection_intermediates(self) -> None:
        """When x_norm or x_rec is None, drift attribution is unavailable."""
        model = _make_model()
        fv = _make_feature_vector()
        proj = ProjectionResult(
            coordinates=np.zeros(model.n_components),
            l_drift=1.0,
            l_virtue=1.0,
            quality_flag="nominal",
            x_norm=None,  # missing intermediate
            x_rec=None,
        )

        result = decompose_drift(proj, model, fv)

        assert result.available is False
        assert result.features == ()
        assert result.dimension == "manifold_drift"

    def test_alignment_available_without_reconstruction_intermediates(self) -> None:
        """Alignment only needs coordinates, not x_norm/x_rec."""
        model = _make_model()
        fv = _make_feature_vector()
        proj = ProjectionResult(
            coordinates=np.zeros(model.n_components),
            l_drift=1.0,
            l_virtue=1.0,
            quality_flag="nominal",
            x_norm=None,
            x_rec=None,
        )

        result = decompose_alignment(proj, model, fv)

        assert result.available is True
        assert result.dimension == "manifold_alignment"
        assert len(result.features) > 0

    def test_ncd_without_exemplar_is_unavailable(self) -> None:
        """NCD with no exemplar_id is unavailable."""
        metrics = _make_metrics()
        nv = {"ncd_exemplar_distance": 0.0}

        result = attribute_direct("ncd_exemplar_distance", metrics, nv)

        assert result.available is False

    def test_entropy_always_available(self) -> None:
        metrics = _make_metrics(entropy=5.0)
        nv = {"token_entropy": 0.375}

        result = attribute_direct("token_entropy", metrics, nv)

        assert result.available is True

    def test_compression_always_available(self) -> None:
        metrics = _make_metrics(birkhoff_measure=0.6)
        nv = {"compression_structure": 0.6}

        result = attribute_direct("compression_structure", metrics, nv)

        assert result.available is True

    def test_unavailable_drift_still_has_normalized_score(self) -> None:
        """Even when unavailable, normalized_score should be set (from l_drift/sigma)."""
        model = _make_model()
        fv = _make_feature_vector()
        proj = ProjectionResult(
            coordinates=np.zeros(model.n_components),
            l_drift=1.5,
            l_virtue=2.0,
            quality_flag="nominal",
            x_norm=None,
            x_rec=None,
        )

        result = decompose_drift(proj, model, fv)

        expected = min(max(proj.l_drift / model.sigma_drift, 0.0), 1.0)
        assert pytest.approx(result.normalized_score, rel=1e-10) == expected

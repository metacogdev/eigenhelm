"""Unit tests for PCA eigenspace projection.

Uses a synthetic EigenspaceModel so tests are independent of a real corpus.
"""

import numpy as np
import pytest


def _make_feature_vector(seed: int = 0):
    """Construct a FeatureVector with known values for testing."""
    from eigenhelm.models import FEATURE_DIM, CodeUnit, FeatureVector

    rng = np.random.default_rng(seed)
    values = rng.standard_normal(FEATURE_DIM)
    unit = CodeUnit(
        source="def foo(): pass",
        language="python",
        name="foo",
        start_line=1,
        end_line=1,
    )
    return FeatureVector(values=values, code_unit=unit)


def test_projection_shape(synthetic_model):
    """Projection coordinates have shape (n_components,)."""
    from eigenhelm.eigenspace.projection import project

    fv = _make_feature_vector()
    result = project(fv, synthetic_model)
    assert result.coordinates.shape == (synthetic_model.n_components,)


def test_projection_l_drift_non_negative(synthetic_model):
    """L_drift is always >= 0."""
    from eigenhelm.eigenspace.projection import project

    fv = _make_feature_vector()
    result = project(fv, synthetic_model)
    assert result.l_drift >= 0.0


def test_projection_l_virtue_non_negative(synthetic_model):
    """L_virtue is always >= 0."""
    from eigenhelm.eigenspace.projection import project

    fv = _make_feature_vector()
    result = project(fv, synthetic_model)
    assert result.l_virtue >= 0.0


def test_projection_deterministic(synthetic_model):
    """Same input → same output."""
    from eigenhelm.eigenspace.projection import project

    fv = _make_feature_vector(seed=7)
    r1 = project(fv, synthetic_model)
    r2 = project(fv, synthetic_model)
    np.testing.assert_array_almost_equal(r1.coordinates, r2.coordinates)
    assert r1.l_drift == pytest.approx(r2.l_drift)
    assert r1.l_virtue == pytest.approx(r2.l_virtue)


def test_projection_partial_flag(synthetic_model):
    """quality_flag is 'partial_input' when FeatureVector has partial_parse."""
    from eigenhelm.eigenspace.projection import project

    from eigenhelm.models import FEATURE_DIM, CodeUnit, FeatureVector

    unit = CodeUnit(source="x", language="python", name="x", start_line=1, end_line=1)
    fv = FeatureVector(
        values=np.zeros(FEATURE_DIM),
        code_unit=unit,
        partial_parse=True,
    )
    result = project(fv, synthetic_model)
    assert result.quality_flag == "partial_input"


def test_projection_quality_nominal(synthetic_model):
    """A random in-distribution vector gets 'nominal' or 'high_drift'."""
    from eigenhelm.eigenspace.projection import project

    fv = _make_feature_vector(seed=42)
    result = project(fv, synthetic_model)
    assert result.quality_flag in ("nominal", "high_drift")


def test_projection_math_consistency(synthetic_model):
    """Verify z = x_norm @ W and L_drift = ||x_rec - x_norm||."""
    from eigenhelm.eigenspace.projection import project

    from eigenhelm.models import FEATURE_DIM

    rng = np.random.default_rng(99)
    from eigenhelm.models import CodeUnit, FeatureVector

    unit = CodeUnit(source="x=1", language="python", name="x", start_line=1, end_line=1)
    fv = FeatureVector(values=rng.standard_normal(FEATURE_DIM), code_unit=unit)

    result = project(fv, synthetic_model)

    W = synthetic_model.projection_matrix
    mu = synthetic_model.mean
    sigma = synthetic_model.std

    x_norm = (fv.values - mu) / sigma
    z_expected = x_norm @ W
    x_rec = z_expected @ W.T
    l_drift_expected = np.linalg.norm(x_rec - x_norm)
    l_virtue_expected = np.linalg.norm(z_expected)

    np.testing.assert_array_almost_equal(result.coordinates, z_expected)
    assert result.l_drift == pytest.approx(l_drift_expected, rel=1e-6)
    assert result.l_virtue == pytest.approx(l_virtue_expected, rel=1e-6)


def test_load_save_model(tmp_path):
    """Round-trip: save synthetic model to .npz, reload, and project."""
    from eigenhelm.eigenspace import load_model, make_synthetic_model
    from eigenhelm.eigenspace.projection import project

    from eigenhelm.models import FEATURE_DIM, CodeUnit, FeatureVector

    model = make_synthetic_model(n_components=4, seed=7)

    path = tmp_path / "test_model.npz"
    np.savez(
        path,
        projection_matrix=model.projection_matrix,
        mean=model.mean,
        std=model.std,
        n_components=model.n_components,
        version=model.version,
        corpus_hash=model.corpus_hash,
    )

    loaded = load_model(path)
    assert loaded.n_components == 4
    np.testing.assert_array_equal(loaded.mean, model.mean)

    unit = CodeUnit(
        source="pass", language="python", name="<m>", start_line=1, end_line=1
    )
    fv = FeatureVector(values=np.ones(FEATURE_DIM), code_unit=unit)
    result = project(fv, loaded)
    assert result.coordinates.shape == (4,)

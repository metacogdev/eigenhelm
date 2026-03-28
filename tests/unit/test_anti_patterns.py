"""Unit tests for anti-pattern detectors (T031, T032)."""

from __future__ import annotations

import numpy as np
from eigenhelm.critic.anti_patterns import (
    detect_anti_patterns,
    detect_builders_trap,
    detect_phantom_authorship,
)

from eigenhelm.models import FEATURE_DIM


def _make_feature_vector(**kwargs) -> np.ndarray:
    """Create a feature vector with specified metric values.

    kwargs: volume, difficulty, effort, complexity, density + optional wl_entropy_target
    """
    fv = np.zeros(FEATURE_DIM, dtype=np.float64)
    fv[0] = kwargs.get("volume", 100.0)
    fv[1] = kwargs.get("difficulty", 10.0)
    fv[2] = kwargs.get("effort", 1000.0)
    fv[3] = kwargs.get("complexity", 5)
    fv[4] = kwargs.get("density", 0.05)

    # WL histogram: default to uniform (high entropy)
    if kwargs.get("low_wl_entropy", False):
        # Concentrate all mass in one bin → very low entropy
        fv[5] = 1.0
    else:
        # Spread evenly across bins → high entropy
        fv[5:69] = 1.0 / 64
    return fv


class TestPhantomAuthorship:
    """Tests for Phantom Authorship detector."""

    def test_fires_on_high_volume_low_wl(self) -> None:
        fv = _make_feature_vector(volume=3000.0, low_wl_entropy=True)
        result = detect_phantom_authorship(fv)
        assert result is not None
        assert result.pattern_name == "phantom_authorship"

    def test_does_not_fire_on_normal_code(self) -> None:
        fv = _make_feature_vector(volume=500.0)
        result = detect_phantom_authorship(fv)
        assert result is None

    def test_does_not_fire_on_high_volume_high_wl(self) -> None:
        fv = _make_feature_vector(volume=3000.0, low_wl_entropy=False)
        result = detect_phantom_authorship(fv)
        assert result is None

    def test_does_not_fire_on_low_volume_low_wl(self) -> None:
        fv = _make_feature_vector(volume=100.0, low_wl_entropy=True)
        result = detect_phantom_authorship(fv)
        assert result is None

    def test_custom_thresholds(self) -> None:
        fv = _make_feature_vector(volume=500.0, low_wl_entropy=True)
        result = detect_phantom_authorship(
            fv, volume_threshold=400.0, wl_entropy_threshold=5.0
        )
        assert result is not None

    def test_deterministic(self) -> None:
        fv = _make_feature_vector(volume=3000.0, low_wl_entropy=True)
        results = [detect_phantom_authorship(fv) for _ in range(10)]
        assert all(r == results[0] for r in results)


class TestBuildersTrap:
    """Tests for Builder's Trap detector."""

    def test_fires_on_low_cd_high_difficulty(self) -> None:
        fv = _make_feature_vector(density=0.01, difficulty=50.0)
        result = detect_builders_trap(fv)
        assert result is not None
        assert result.pattern_name == "builders_trap"

    def test_does_not_fire_on_normal_code(self) -> None:
        fv = _make_feature_vector(density=0.05, difficulty=10.0)
        result = detect_builders_trap(fv)
        assert result is None

    def test_does_not_fire_on_low_cd_low_difficulty(self) -> None:
        fv = _make_feature_vector(density=0.01, difficulty=5.0)
        result = detect_builders_trap(fv)
        assert result is None

    def test_does_not_fire_on_high_cd_high_difficulty(self) -> None:
        fv = _make_feature_vector(density=0.1, difficulty=50.0)
        result = detect_builders_trap(fv)
        assert result is None

    def test_custom_thresholds(self) -> None:
        fv = _make_feature_vector(density=0.05, difficulty=20.0)
        result = detect_builders_trap(fv, cd_threshold=0.06, difficulty_threshold=15.0)
        assert result is not None

    def test_deterministic(self) -> None:
        fv = _make_feature_vector(density=0.01, difficulty=50.0)
        results = [detect_builders_trap(fv) for _ in range(10)]
        assert all(r == results[0] for r in results)


class TestDetectAntiPatterns:
    """Tests for the combined detect_anti_patterns() function."""

    def test_both_patterns_can_fire(self) -> None:
        fv = _make_feature_vector(
            volume=3000.0, low_wl_entropy=True, density=0.01, difficulty=50.0
        )
        violations = detect_anti_patterns(fv)
        names = {v.pattern_name for v in violations}
        assert "phantom_authorship" in names
        assert "builders_trap" in names

    def test_no_patterns_on_clean_code(self) -> None:
        fv = _make_feature_vector(volume=500.0, density=0.05, difficulty=10.0)
        violations = detect_anti_patterns(fv)
        assert violations == []

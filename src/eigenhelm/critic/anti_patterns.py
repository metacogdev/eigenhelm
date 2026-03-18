"""Anti-pattern detectors for code quality failure modes.

Detects two anti-patterns from metric signatures:
  - Phantom Authorship: likely AI-generated template repetition
  - Builder's Trap: excessive abstraction relative to functional surface
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class AntiPatternViolation:
    """A named detection of a specific code quality failure mode."""

    pattern_name: str  # "phantom_authorship" | "builders_trap"
    explanation: str  # Human-readable description
    triggering_metrics: dict[str, float]  # Metric values that triggered detection


# Fallback thresholds when calibration stats are unavailable
_DEFAULT_VOLUME_THRESHOLD = 2000.0
_DEFAULT_WL_ENTROPY_THRESHOLD = 3.0  # bits
_DEFAULT_CD_THRESHOLD = 0.02
_DEFAULT_DIFFICULTY_THRESHOLD = 30.0


def _wl_histogram_entropy(fv_values: np.ndarray) -> float:
    """Compute Shannon entropy of the WL histogram bins (indices 5:69)."""
    hist = fv_values[5:69]
    # Normalize to probabilities (should already sum to ~1.0)
    total = hist.sum()
    if total <= 0:
        return 0.0
    probs = hist / total
    entropy = 0.0
    for p in probs:
        if p > 0:
            entropy -= p * math.log2(p)
    return entropy


def detect_phantom_authorship(
    fv_values: np.ndarray,
    *,
    volume_threshold: float | None = None,
    wl_entropy_threshold: float | None = None,
) -> AntiPatternViolation | None:
    """Detect Phantom Authorship: high Halstead Volume + low WL hash consistency.

    Trigger: Volume > corpus 90th percentile AND WL entropy < corpus 10th percentile.
    Uses fallback absolute thresholds when calibration values not provided.
    """
    vol_thresh = volume_threshold if volume_threshold is not None else _DEFAULT_VOLUME_THRESHOLD
    ent_thresh = (
        wl_entropy_threshold if wl_entropy_threshold is not None else _DEFAULT_WL_ENTROPY_THRESHOLD
    )

    volume = float(fv_values[0])  # Halstead Volume
    wl_entropy = _wl_histogram_entropy(fv_values)

    if volume > vol_thresh and wl_entropy < ent_thresh:
        return AntiPatternViolation(
            pattern_name="phantom_authorship",
            explanation=(
                f"High Halstead Volume ({volume:.0f} > {vol_thresh:.0f}) combined with "
                f"low WL hash diversity ({wl_entropy:.2f} < {ent_thresh:.1f} bits) "
                "suggests AI-generated template repetition."
            ),
            triggering_metrics={"halstead_volume": volume, "wl_entropy": wl_entropy},
        )
    return None


def detect_builders_trap(
    fv_values: np.ndarray,
    *,
    cd_threshold: float | None = None,
    difficulty_threshold: float | None = None,
) -> AntiPatternViolation | None:
    """Detect Builder's Trap: low Cyclomatic Density + high Halstead Difficulty.

    Trigger: CD < 0.02 AND Difficulty > corpus 80th percentile.
    Uses fallback absolute thresholds when calibration values not provided.
    """
    cd_thresh = cd_threshold if cd_threshold is not None else _DEFAULT_CD_THRESHOLD
    diff_thresh = (
        difficulty_threshold if difficulty_threshold is not None else _DEFAULT_DIFFICULTY_THRESHOLD
    )

    cyclomatic_density = float(fv_values[4])
    difficulty = float(fv_values[1])  # Halstead Difficulty

    if cyclomatic_density < cd_thresh and difficulty > diff_thresh:
        return AntiPatternViolation(
            pattern_name="builders_trap",
            explanation=(
                f"Low Cyclomatic Density ({cyclomatic_density:.4f} < {cd_thresh}) combined with "
                f"high Halstead Difficulty ({difficulty:.1f} > {diff_thresh:.0f}) "
                "suggests excessive abstraction relative to functional surface."
            ),
            triggering_metrics={
                "cyclomatic_density": cyclomatic_density,
                "halstead_difficulty": difficulty,
            },
        )
    return None


def detect_anti_patterns(
    fv_values: np.ndarray,
    *,
    volume_threshold: float | None = None,
    wl_entropy_threshold: float | None = None,
    cd_threshold: float | None = None,
    difficulty_threshold: float | None = None,
) -> list[AntiPatternViolation]:
    """Run all anti-pattern detectors and return violations found."""
    violations: list[AntiPatternViolation] = []

    result = detect_phantom_authorship(
        fv_values,
        volume_threshold=volume_threshold,
        wl_entropy_threshold=wl_entropy_threshold,
    )
    if result is not None:
        violations.append(result)

    result = detect_builders_trap(
        fv_values,
        cd_threshold=cd_threshold,
        difficulty_threshold=difficulty_threshold,
    )
    if result is not None:
        violations.append(result)

    return violations

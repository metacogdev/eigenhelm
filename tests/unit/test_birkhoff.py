"""Unit tests for birkhoff_measure() — written FIRST (TDD), must fail before implementation.

Formula: M_Z = (N·H − K) / (N·H)
  N = raw_bytes, H = entropy (bits/byte), K = compressed_bytes
  Clamped to [0.0, 1.0]; returns 0.0 when N·H == 0.
"""

from eigenhelm.critic.birkhoff import birkhoff_measure


def test_zero_n_times_h_from_zero_n_returns_zero():
    # N=0 → N·H=0 → undefined → 0.0
    assert birkhoff_measure(entropy=0.0, raw_bytes=0, compressed_bytes=0) == 0.0


def test_zero_entropy_any_n_returns_zero():
    # H=0 → N·H=0 regardless of N → 0.0
    assert birkhoff_measure(entropy=0.0, raw_bytes=100, compressed_bytes=50) == 0.0


def test_k_greater_than_nh_clamped_to_zero():
    # entropy=1.0, raw_bytes=5 → N·H=5
    # compressed_bytes=20 → (5-20)/5 = -3 → clamp to 0.0
    assert birkhoff_measure(entropy=1.0, raw_bytes=5, compressed_bytes=20) == 0.0


def test_k_exactly_equals_nh_returns_zero():
    # entropy=4.0, raw_bytes=10 → N·H=40
    # compressed_bytes=40 → (40-40)/40 = 0.0
    result = birkhoff_measure(entropy=4.0, raw_bytes=10, compressed_bytes=40)
    assert result == 0.0


def test_typical_values_in_range():
    # entropy=4.0, raw_bytes=100, compressed_bytes=50
    # N·H=400, K=50 → M_Z = (400-50)/400 = 0.875
    result = birkhoff_measure(entropy=4.0, raw_bytes=100, compressed_bytes=50)
    assert abs(result - 0.875) < 1e-9


def test_high_structure_near_one():
    # entropy=6.0, raw_bytes=1000, compressed_bytes=1
    # N·H=6000, K=1 → M_Z = 5999/6000 ≈ 0.9998
    result = birkhoff_measure(entropy=6.0, raw_bytes=1000, compressed_bytes=1)
    assert result > 0.99


def test_always_in_unit_interval():
    cases = [
        (0.0, 0, 0),
        (0.0, 100, 50),
        (4.0, 100, 50),
        (8.0, 1000, 950),
        (3.0, 200, 300),  # K > N·H → clamped to 0.0
    ]
    for entropy, raw, compressed in cases:
        result = birkhoff_measure(entropy, raw, compressed)
        assert 0.0 <= result <= 1.0, (
            f"Out of [0,1] for entropy={entropy}, raw={raw}, compressed={compressed}: {result}"
        )


def test_returns_float():
    assert isinstance(birkhoff_measure(4.0, 100, 50), float)


def test_deterministic():
    assert birkhoff_measure(4.0, 100, 50) == birkhoff_measure(4.0, 100, 50)

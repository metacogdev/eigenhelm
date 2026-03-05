"""Unit tests for shannon_entropy() — written FIRST (TDD), must fail before implementation."""

from eigenhelm.critic.entropy import shannon_entropy


def test_empty_source_returns_zero():
    assert shannon_entropy("") == 0.0


def test_single_char_source_returns_zero():
    # All bytes identical → p=1 → H = -1·log2(1) = 0
    assert shannon_entropy("a") == 0.0


def test_repeated_char_returns_zero():
    assert shannon_entropy("a" * 1000) == 0.0


def test_two_equally_probable_bytes():
    # Two distinct bytes each appearing 50% → H = 1.0 bit/byte
    src = "ab" * 100
    h = shannon_entropy(src)
    assert abs(h - 1.0) < 1e-9


def test_uniform_ascii_byte_distribution():
    # 128 distinct ASCII bytes each appearing once → H = log2(128) = 7.0 exactly
    src = bytes(range(128)).decode("ascii")
    h = shannon_entropy(src)
    assert abs(h - 7.0) < 1e-9


def test_high_variety_bytes_high_entropy():
    # latin-1 chars cover a wide byte range; entropy should be well above 5.0
    # (UTF-8 re-encoding of latin-1 bytes 128-255 produces 2-byte sequences,
    # so entropy is ~6.25 rather than 8.0 — still high, confirming the signal works)
    src = bytes(range(256)).decode("latin-1")
    h = shannon_entropy(src)
    assert h > 5.0


def test_typical_code_range():
    source = (
        "def quicksort(arr):\n"
        "    if len(arr) <= 1:\n"
        "        return arr\n"
        "    pivot = arr[len(arr) // 2]\n"
        "    left = [x for x in arr if x < pivot]\n"
        "    mid  = [x for x in arr if x == pivot]\n"
        "    right = [x for x in arr if x > pivot]\n"
        "    return quicksort(left) + mid + quicksort(right)\n"
    )
    h = shannon_entropy(source)
    assert 3.5 <= h <= 5.5


def test_range_always_zero_to_eight():
    for src in ["", "a", "ab", "abc" * 100]:
        h = shannon_entropy(src)
        assert 0.0 <= h <= 8.0, f"Out of range for {src!r}: {h}"


def test_returns_float():
    assert isinstance(shannon_entropy("hello world"), float)


def test_deterministic():
    src = "def foo(): return 42\n"
    assert shannon_entropy(src) == shannon_entropy(src)

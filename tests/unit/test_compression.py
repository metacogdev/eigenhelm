"""Unit tests for compression_ratio() — written FIRST (TDD), must fail before implementation."""

import os

from eigenhelm.critic.compression import compression_ratio


def test_empty_source_returns_none():
    assert compression_ratio("") is None


def test_source_below_default_threshold_returns_none():
    # default min_bytes=50; 30-byte source → None
    short = "x" * 30
    assert len(short.encode()) < 50
    assert compression_ratio(short) is None


def test_source_at_49_bytes_returns_none():
    src = "a" * 49
    assert len(src.encode("utf-8")) == 49
    assert compression_ratio(src) is None


def test_source_at_50_bytes_returns_ratio():
    src = "abcde" * 10  # exactly 50 bytes
    assert len(src.encode("utf-8")) == 50
    result = compression_ratio(src)
    assert result is not None
    assert isinstance(result, float)
    assert result > 0.0


def test_repetitive_source_low_ratio():
    # Highly repetitive → compresses well → ratio well below 1.0
    src = "aaaa" * 200  # 800 bytes, maximally repetitive
    ratio = compression_ratio(src)
    assert ratio is not None
    assert ratio < 0.5


def test_random_source_high_ratio():
    # Near-random bytes → hard to compress → ratio close to or above 1.0
    raw = os.urandom(300)
    src = raw.decode("latin-1")
    ratio = compression_ratio(src)
    assert ratio is not None
    assert ratio > 0.5


def test_custom_min_bytes_below_threshold():
    src = "hello " * 12  # 72 bytes
    assert len(src.encode()) == 72
    assert compression_ratio(src, min_bytes=100) is None


def test_custom_min_bytes_above_threshold():
    src = "hello world " * 10  # 120 bytes
    assert len(src.encode()) >= 100
    result = compression_ratio(src, min_bytes=100)
    assert result is not None
    assert isinstance(result, float)


def test_returns_float_or_none():
    src = "x" * 200
    result = compression_ratio(src)
    assert result is None or isinstance(result, float)


def test_deterministic():
    src = "def foo():\n    pass\n" * 5
    assert compression_ratio(src) == compression_ratio(src)

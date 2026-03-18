"""Unit tests for config data models (ThresholdConfig, PathRule, ProjectConfig)."""

from __future__ import annotations

import pytest

from eigenhelm.config.models import PathRule, ProjectConfig, ThresholdConfig


class TestThresholdConfig:
    def test_defaults(self):
        t = ThresholdConfig()
        assert t.accept is None
        assert t.reject is None

    def test_custom_values(self):
        t = ThresholdConfig(accept=0.2, reject=0.8)
        assert t.accept == 0.2
        assert t.reject == 0.8

    def test_accept_must_be_less_than_reject(self):
        with pytest.raises(ValueError, match="accept must be < reject"):
            ThresholdConfig(accept=0.7, reject=0.3)

    def test_equal_accept_reject_raises(self):
        with pytest.raises(ValueError, match="accept must be < reject"):
            ThresholdConfig(accept=0.5, reject=0.5)

    def test_accept_out_of_range_low(self):
        with pytest.raises(ValueError, match="accept must be in"):
            ThresholdConfig(accept=-0.1, reject=0.7)

    def test_accept_out_of_range_high(self):
        with pytest.raises(ValueError, match="accept must be in"):
            ThresholdConfig(accept=1.1, reject=1.5)

    def test_reject_out_of_range(self):
        with pytest.raises(ValueError, match="reject must be in"):
            ThresholdConfig(accept=0.3, reject=1.1)

    def test_frozen(self):
        t = ThresholdConfig()
        with pytest.raises((AttributeError, TypeError)):
            t.accept = 0.5  # type: ignore[misc]


class TestPathRule:
    def test_basic(self):
        r = PathRule(glob="src/**")
        assert r.glob == "src/**"
        assert r.thresholds == ThresholdConfig()

    def test_custom_thresholds(self):
        t = ThresholdConfig(accept=0.1, reject=0.9)
        r = PathRule(glob="scripts/**", thresholds=t)
        assert r.thresholds.accept == 0.1

    def test_empty_glob_raises(self):
        with pytest.raises(ValueError, match="non-empty"):
            PathRule(glob="")

    def test_matches_exact(self):
        r = PathRule(glob="src/core/utils.py")
        assert r.matches("src/core/utils.py")
        assert not r.matches("src/core/other.py")

    def test_matches_wildcard(self):
        r = PathRule(glob="src/**")
        assert r.matches("src/anything/deep/file.py")

    def test_matches_star(self):
        r = PathRule(glob="scripts/*.py")
        assert r.matches("scripts/build.py")
        # fnmatch treats * as matching any characters including /
        assert not r.matches("other/build.py")


class TestProjectConfig:
    def test_defaults(self):
        cfg = ProjectConfig()
        assert cfg.model is None
        assert cfg.language is None
        assert cfg.strict is False
        assert cfg.thresholds == ThresholdConfig()
        assert cfg.paths == ()
        assert cfg.language_overrides == {}

    def test_thresholds_for_no_match(self):
        cfg = ProjectConfig()
        result = cfg.thresholds_for("src/foo.py")
        assert result == cfg.thresholds

    def test_thresholds_for_single_match(self):
        t = ThresholdConfig(accept=0.1, reject=0.9)
        rule = PathRule(glob="src/**", thresholds=t)
        cfg = ProjectConfig(paths=(rule,))
        result = cfg.thresholds_for("src/core/utils.py")
        assert result == t

    def test_thresholds_for_last_match_wins(self):
        t1 = ThresholdConfig(accept=0.1, reject=0.9)
        t2 = ThresholdConfig(accept=0.2, reject=0.8)
        rule1 = PathRule(glob="src/**", thresholds=t1)
        rule2 = PathRule(glob="src/core/**", thresholds=t2)
        cfg = ProjectConfig(paths=(rule1, rule2))
        # Both match — last wins (rule2)
        result = cfg.thresholds_for("src/core/utils.py")
        assert result == t2

    def test_thresholds_for_only_first_matches(self):
        t1 = ThresholdConfig(accept=0.1, reject=0.9)
        t2 = ThresholdConfig(accept=0.2, reject=0.8)
        rule1 = PathRule(glob="src/**", thresholds=t1)
        rule2 = PathRule(glob="scripts/**", thresholds=t2)
        cfg = ProjectConfig(paths=(rule1, rule2))
        result = cfg.thresholds_for("src/utils.py")
        assert result == t1

    def test_thresholds_for_no_rules_returns_global(self):
        global_t = ThresholdConfig(accept=0.15, reject=0.85)
        cfg = ProjectConfig(thresholds=global_t)
        result = cfg.thresholds_for("anything.py")
        assert result == global_t

    def test_language_overrides_invalid_key_raises(self):
        with pytest.raises(ValueError, match="must start with '.'"):
            ProjectConfig(language_overrides={"jsx": "javascript"})

    def test_language_overrides_valid(self):
        cfg = ProjectConfig(language_overrides={".jsx": "javascript"})
        assert cfg.language_overrides == {".jsx": "javascript"}

    def test_frozen(self):
        cfg = ProjectConfig()
        with pytest.raises((AttributeError, TypeError)):
            cfg.model = "something"  # type: ignore[misc]

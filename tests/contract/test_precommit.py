"""Contract tests for eigenhelm-check pre-commit hook."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from eigenhelm.cli.precommit import EvaluationCache, CacheEntry, _hash_file, main

pytestmark = pytest.mark.contract


def _make_mock_response(decision="accept", score=0.2):
    resp = MagicMock()
    resp.decision = decision
    resp.score = score
    resp.structural_confidence = "low"
    resp.critique.violations = []
    resp.warning = None
    return resp


class TestEvaluationCache:
    def test_empty_cache_returns_none(self, tmp_path):
        cache = EvaluationCache(tmp_path / "cache.json", config_hash="abc")
        assert cache.get("file.py", "hash123") is None

    def test_set_and_get_hit(self, tmp_path):
        cache = EvaluationCache(tmp_path / "cache.json", config_hash="abc")
        cache.set("file.py", CacheEntry("hash123", "accept", 0.2))
        result = cache.get("file.py", "hash123")
        assert result is not None
        assert result.decision == "accept"

    def test_get_miss_on_different_hash(self, tmp_path):
        cache = EvaluationCache(tmp_path / "cache.json", config_hash="abc")
        cache.set("file.py", CacheEntry("hash123", "accept", 0.2))
        result = cache.get("file.py", "different_hash")
        assert result is None

    def test_save_and_reload(self, tmp_path):
        cache_path = tmp_path / ".eigenhelm" / "cache.json"
        cache1 = EvaluationCache(cache_path, config_hash="cfg_hash")
        cache1.set("file.py", CacheEntry("content_hash", "warn", 0.5))
        cache1.save()

        cache2 = EvaluationCache(cache_path, config_hash="cfg_hash")
        result = cache2.get("file.py", "content_hash")
        assert result is not None
        assert result.decision == "warn"
        assert result.score == 0.5

    def test_config_change_invalidates_cache(self, tmp_path):
        cache_path = tmp_path / ".eigenhelm" / "cache.json"
        cache1 = EvaluationCache(cache_path, config_hash="old_hash")
        cache1.set("file.py", CacheEntry("content_hash", "accept", 0.2))
        cache1.save()

        # Load with different config hash — should be invalidated
        cache2 = EvaluationCache(cache_path, config_hash="new_hash")
        result = cache2.get("file.py", "content_hash")
        assert result is None


class TestPrecommitMain:
    def _setup_staged_file(self, tmp_path, filename="test.py", content="x = 1\n"):
        f = tmp_path / filename
        f.write_text(content)
        return f

    def test_no_staged_files_exits_0(self, tmp_path):
        with patch("eigenhelm.cli.precommit._get_staged_files", return_value=[]):
            code = main([])
        assert code == 0

    def test_staged_accept_exits_0(self, tmp_path):
        f = self._setup_staged_file(tmp_path)
        mock_resp = _make_mock_response("accept")
        with (
            patch("eigenhelm.cli.precommit._get_staged_files", return_value=[f]),
            patch("eigenhelm.cli.precommit.EvaluationCache.save"),
            patch("eigenhelm.helm.DynamicHelm.evaluate", return_value=mock_resp),
        ):
            code = main([])
        assert code == 0

    def test_staged_reject_exits_1(self, tmp_path):
        f = self._setup_staged_file(tmp_path)
        mock_resp = _make_mock_response("reject", score=0.9)
        with (
            patch("eigenhelm.cli.precommit._get_staged_files", return_value=[f]),
            patch("eigenhelm.cli.precommit.EvaluationCache.save"),
            patch("eigenhelm.helm.DynamicHelm.evaluate", return_value=mock_resp),
        ):
            code = main([])
        assert code == 1

    def test_warn_default_exits_0(self, tmp_path):
        f = self._setup_staged_file(tmp_path)
        mock_resp = _make_mock_response("warn", score=0.5)
        with (
            patch("eigenhelm.cli.precommit._get_staged_files", return_value=[f]),
            patch("eigenhelm.cli.precommit.EvaluationCache.save"),
            patch("eigenhelm.helm.DynamicHelm.evaluate", return_value=mock_resp),
        ):
            code = main([])
        assert code == 0

    def test_strict_warn_exits_1(self, tmp_path):
        f = self._setup_staged_file(tmp_path)
        mock_resp = _make_mock_response("warn", score=0.5)
        with (
            patch("eigenhelm.cli.precommit._get_staged_files", return_value=[f]),
            patch("eigenhelm.cli.precommit.EvaluationCache.save"),
            patch("eigenhelm.helm.DynamicHelm.evaluate", return_value=mock_resp),
        ):
            code = main(["--strict"])
        assert code == 1

    def test_lenient_overrides_config_strict(self, tmp_path):
        """--lenient flag overrides config strict=true."""
        f = self._setup_staged_file(tmp_path)
        mock_resp = _make_mock_response("warn", score=0.5)
        mock_config = MagicMock()
        mock_config.strict = True
        mock_config.model = None
        mock_config.language_overrides = {}
        mock_config.thresholds_for.return_value = MagicMock(
            accept=0.3, reject=0.7
        )
        with (
            patch("eigenhelm.cli.precommit._get_staged_files", return_value=[f]),
            patch("eigenhelm.cli.precommit.EvaluationCache.save"),
            patch("eigenhelm.helm.DynamicHelm.evaluate", return_value=mock_resp),
            patch("eigenhelm.cli.precommit.find_config", return_value=tmp_path / "cfg"),
            patch("eigenhelm.cli.precommit.load_config", return_value=mock_config),
        ):
            code = main(["--lenient"])
        # With --lenient, warn should not block even if config.strict=True
        assert code == 0

    def test_strict_and_lenient_mutually_exclusive(self):
        """--strict and --lenient cannot be used together."""
        with pytest.raises(SystemExit):
            main(["--strict", "--lenient"])

    def test_cache_hit_skips_evaluation(self, tmp_path):
        f = self._setup_staged_file(tmp_path, content="x = 1\n")
        content_hash = _hash_file(f.read_bytes())

        cache_path = tmp_path / ".eigenhelm" / "cache.json"
        cache_path.parent.mkdir(parents=True)
        cache_data = {
            "version": 1,
            "config_hash": "",
            "entries": {
                str(f): {"content_hash": content_hash, "decision": "accept", "score": 0.1}
            },
        }
        cache_path.write_text(json.dumps(cache_data))

        with (
            patch("eigenhelm.cli.precommit._get_staged_files", return_value=[f]),
            patch("eigenhelm.cli.precommit._CACHE_FILE", cache_path),
            patch("eigenhelm.cli.precommit.EvaluationCache.save"),
            patch("eigenhelm.helm.DynamicHelm.evaluate") as mock_eval,
        ):
            code = main([])
            # Should not have called evaluate — cache hit
            mock_eval.assert_not_called()
        assert code == 0

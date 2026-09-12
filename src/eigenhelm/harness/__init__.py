"""Evaluation harness — compare two corpora with statistical testing."""

from eigenhelm.harness.report import CorpusStats, HarnessReport
from eigenhelm.harness.runner import run_harness

__all__ = ["SIGNIFICANCE_ALPHA", "CorpusStats", "HarnessReport", "run_harness"]

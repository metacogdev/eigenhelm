"""Contract tests for eigenhelm-inspect language metadata display (009 T018)."""

from __future__ import annotations

import json
from io import StringIO
from pathlib import Path

import numpy as np

from eigenhelm.cli.inspect import main
from eigenhelm.models import FEATURE_DIM, EigenspaceModel, TrainingResult
from eigenhelm.training.serialization import save_model


def _make_model_file(
    tmp_path: Path,
    name: str,
    *,
    language: str | None = None,
    corpus_class: str | None = None,
    n_training_files: int = 0,
) -> Path:
    """Create a minimal .npz model file with configurable metadata."""
    rng = np.random.default_rng(42)
    W = np.eye(FEATURE_DIM, 3, dtype=np.float64)
    mean = rng.standard_normal(FEATURE_DIM).astype(np.float64)
    std = np.abs(rng.standard_normal(FEATURE_DIM).astype(np.float64)) + 0.1

    model = EigenspaceModel(
        projection_matrix=W,
        mean=mean,
        std=std,
        n_components=3,
        version="test",
        corpus_hash="c" * 64,
        sigma_drift=1.5,
        sigma_virtue=2.0,
        language=language,
        corpus_class=corpus_class,
        n_training_files=n_training_files,
    )
    evr = np.array([0.5, 0.3, 0.1], dtype=np.float64)
    result = TrainingResult(
        model=model,
        explained_variance_ratio=evr,
        cumulative_variance=0.9,
        n_files_processed=n_training_files,
        n_files_skipped=0,
        n_units_extracted=50,
        n_vectors_excluded=0,
    )
    out = tmp_path / name
    save_model(result, out)
    return out


def _capture_inspect(model_path: Path, *, as_json: bool = False) -> str:
    """Run eigenhelm-inspect and capture stdout."""
    import sys

    old_stdout = sys.stdout
    sys.stdout = captured = StringIO()
    try:
        argv = [str(model_path)]
        if as_json:
            argv.append("--json")
        main(argv)
    except SystemExit:
        pass
    finally:
        sys.stdout = old_stdout
    return captured.getvalue()


class TestInspectHumanOutput:
    """Contract: human output shows language metadata."""

    def test_metadata_displayed(self, tmp_path: Path) -> None:
        model = _make_model_file(
            tmp_path,
            "js_model.npz",
            language="javascript",
            corpus_class="A",
            n_training_files=250,
        )
        output = _capture_inspect(model)
        assert "Language:     javascript" in output
        assert "Corpus class: A" in output
        assert "Training files: 250" in output

    def test_backward_compat_defaults(self, tmp_path: Path) -> None:
        """Pre-009 model shows 'unknown' for missing metadata."""
        model = _make_model_file(tmp_path, "old_model.npz")
        output = _capture_inspect(model)
        assert "Language:     unknown" in output
        assert "Corpus class: unknown" in output


class TestInspectJsonOutput:
    """Contract: JSON output includes language metadata keys."""

    def test_json_contains_metadata(self, tmp_path: Path) -> None:
        model = _make_model_file(
            tmp_path,
            "go_model.npz",
            language="go",
            corpus_class="A",
            n_training_files=180,
        )
        output = _capture_inspect(model, as_json=True)
        data = json.loads(output)
        assert data["language"] == "go"
        assert data["corpus_class"] == "A"
        assert data["n_training_files"] == 180

    def test_json_backward_compat(self, tmp_path: Path) -> None:
        """Pre-009 model has None for language in JSON."""
        model = _make_model_file(tmp_path, "old_model.npz")
        output = _capture_inspect(model, as_json=True)
        data = json.loads(output)
        assert data["language"] is None
        assert data["corpus_class"] is None
        assert data["n_training_files"] == 0

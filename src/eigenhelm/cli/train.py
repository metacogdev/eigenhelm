"""eigenhelm-train: Train a PCA eigenspace model from a code corpus."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from eigenhelm.models import TrainingResult


def format_training_report(
    result: TrainingResult,
    corpus_dir: Path,
    output_path: Path,
    *,
    auto_selected: bool = True,
) -> str:
    """Format the training summary report for stdout.

    Matches the CLI contract output format from contracts/itraining_pipeline.md.
    """

    model = result.model
    evr = result.explained_variance_ratio

    per_pc = "  ".join(f"PC{i + 1}: {v * 100:.1f}%" for i, v in enumerate(evr))

    lines = [
        "eigenhelm-train: Training complete",
        f"  Corpus:     {corpus_dir}",
        f"  Files:      {result.n_files_processed} processed, {result.n_files_skipped} skipped",
        f"  Code units: {result.n_units_extracted} extracted, "
        f"{result.n_vectors_excluded} excluded (NaN/Inf)",
        f"  Components: {model.n_components} ({'auto-selected' if auto_selected else 'explicit'})",
        f"  Variance:   {result.cumulative_variance * 100:.1f}% cumulative",
        f"    {per_pc}",
        f"  Corpus hash: {model.corpus_hash}",
        f"  Version:    {model.version}",
        f"  Output:     {output_path}",
    ]

    if result.calibration is not None:
        cal = result.calibration
        lines.append(
            f"  Calibration:  sigma_drift={cal.sigma_drift:.4f}"
            f"  sigma_virtue={cal.sigma_virtue:.4f}"
            f"  (p{cal.percentile:.0f} of {cal.n_projections} training projections)"
        )

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    """Entry point for eigenhelm-train CLI.

    Exit codes:
        0 — success
        1 — validation error (bad args, no files, etc.)
        2 — runtime error (extraction failure, etc.)
    """
    parser = argparse.ArgumentParser(
        prog="eigenhelm-train",
        description="Train a PCA eigenspace model from a code corpus.",
    )
    parser.add_argument(
        "corpus_dir",
        metavar="corpus-dir",
        type=Path,
        help="Root directory of the code corpus",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        type=Path,
        metavar="PATH",
        help="Output .npz file path",
    )
    parser.add_argument(
        "--n-components",
        type=int,
        default=None,
        metavar="INT",
        help="Explicit number of principal components",
    )
    parser.add_argument(
        "--variance-threshold",
        type=float,
        default=0.90,
        metavar="FLOAT",
        help="Minimum cumulative explained variance for auto-select (default: 0.90)",
    )
    parser.add_argument(
        "--version",
        default=None,
        metavar="TEXT",
        help="Model version string (default: package version)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing output file",
    )

    args = parser.parse_args(argv)

    from eigenhelm.training import save_model, train_eigenspace

    try:
        result = train_eigenspace(
            corpus_dir=args.corpus_dir,
            n_components=args.n_components,
            variance_threshold=args.variance_threshold,
            version=args.version,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"eigenhelm-train: error: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"eigenhelm-train: runtime error: {exc}", file=sys.stderr)
        sys.exit(2)

    try:
        save_model(result, args.output, force=args.force)
    except FileExistsError as exc:
        print(f"eigenhelm-train: error: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"eigenhelm-train: runtime error: {exc}", file=sys.stderr)
        sys.exit(2)

    print(
        format_training_report(
            result,
            args.corpus_dir,
            args.output,
            auto_selected=args.n_components is None,
        )
    )
    sys.exit(0)

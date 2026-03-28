"""eigenhelm-inspect: Inspect a trained .npz eigenspace model."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> None:
    """Entry point for eigenhelm-inspect CLI.

    Exit codes:
        0 — success
        1 — invalid model file (missing keys, bad format)
    """
    parser = argparse.ArgumentParser(
        prog="eigenhelm-inspect",
        description="Inspect a trained .npz eigenspace model.",
    )
    parser.add_argument(
        "model_path",
        metavar="model-path",
        type=Path,
        help="Path to a .npz eigenspace model",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Output as JSON instead of plain text",
    )

    args = parser.parse_args(argv)

    from eigenhelm.training import inspect_model

    try:
        info = inspect_model(args.model_path)
    except FileNotFoundError as exc:
        print(f"eigenhelm-inspect: error: {exc}", file=sys.stderr)
        sys.exit(1)
    except KeyError as exc:
        print(f"eigenhelm-inspect: invalid model file: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"eigenhelm-inspect: error: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.as_json:
        evr = info["explained_variance_ratio"]
        out = {
            "language": info.get("language"),
            "corpus_class": info.get("corpus_class"),
            "n_training_files": info.get("n_training_files", 0),
            "version": info["version"],
            "n_components": info["n_components"],
            "corpus_hash": info["corpus_hash"],
            "projection_shape": list(info["projection_shape"]),
            "cumulative_variance": info["cumulative_variance"],
            "explained_variance_ratio": evr.tolist() if evr is not None else None,
            "mean_range": list(info["mean_range"]),
            "std_range": list(info["std_range"]),
            "sigma_drift": info["sigma_drift"],
            "sigma_virtue": info["sigma_virtue"],
            "n_exemplars": info.get("n_exemplars", 0),
            "calibrated_accept": info.get("calibrated_accept"),
            "calibrated_reject": info.get("calibrated_reject"),
            "score_distribution": info.get("score_distribution"),
        }
        print(json.dumps(out, indent=2))
    else:
        evr = info["explained_variance_ratio"]
        if evr is not None:
            per_pc = "  ".join(f"PC{i + 1}: {v * 100:.1f}%" for i, v in enumerate(evr))
            variance_line = f"{info['cumulative_variance'] * 100:.1f}% cumulative"
        else:
            per_pc = "(not available)"
            variance_line = "N/A"

        lang_label = info.get("language") or "unknown"
        class_label = info.get("corpus_class") or "unknown"
        n_train = info.get("n_training_files", 0)

        lines = [
            "eigenhelm-inspect: Model summary",
            f"  Language:     {lang_label}",
            f"  Corpus class: {class_label}",
            f"  Training files: {n_train}",
            f"  Version:      {info['version']}",
            f"  Components:   {info['n_components']}",
            f"  Corpus hash:  {info['corpus_hash']}",
            f"  Projection:   {info['projection_shape']}",
            f"  Variance:     {variance_line}",
            f"    {per_pc}",
            f"  Feature mean: [{info['mean_range'][0]:.2f}, {info['mean_range'][1]:.2f}] (range)",
            f"  Feature std:  [{info['std_range'][0]:.2f}, {info['std_range'][1]:.2f}] (range)",
        ]

        sd = info["sigma_drift"]
        sv = info["sigma_virtue"]
        if sd is not None and sv is not None:
            lines.append(f"  Calibration:  sigma_drift={sd:.4f}  sigma_virtue={sv:.4f}")

        n_ex = info.get("n_exemplars", 0)
        if n_ex > 0:
            lines.append(f"  Exemplars:    {n_ex}")

        ca = info.get("calibrated_accept")
        cr = info.get("calibrated_reject")
        if ca is not None and cr is not None:
            lines.append(
                f"  Thresholds:   accept < {ca:.4f} (p25)  reject > {cr:.4f} (p75)"
            )

        score_dist = info.get("score_distribution")
        if score_dist is not None:
            lines.append(
                f"  Score dist:   min={score_dist['min']:.3f}  "
                f"p10={score_dist['p10']:.3f}  p25={score_dist['p25']:.3f}  "
                f"median={score_dist['median']:.3f}  p75={score_dist['p75']:.3f}  "
                f"p90={score_dist['p90']:.3f}  max={score_dist['max']:.3f}"
            )

        print("\n".join(lines))

    sys.exit(0)

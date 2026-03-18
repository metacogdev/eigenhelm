"""JSON output formatting for eigenhelm evaluation results.

Extracted from eigenhelm.cli.evaluate to allow reuse by other output modules.
"""

from __future__ import annotations

import json
from pathlib import Path

from eigenhelm.attribution.serialize import attribution_to_dict
from eigenhelm.helm.models import EvaluationResponse


def format_results_json(
    results: list[tuple[Path | str, EvaluationResponse]],
) -> str:
    """Format evaluation results as JSON matching the BatchResponse schema.

    Returns a JSON string with keys:
      - results: list of per-file result objects
      - summary: aggregate statistics
    """
    result_dicts = []
    for path, resp in results:
        violations = [
            {
                "dimension": v.dimension,
                "raw_value": v.raw_value,
                "normalized_value": v.normalized_value,
                "contribution": v.contribution,
            }
            for v in resp.critique.violations
        ]
        contributions = [
            {
                "dimension": c.dimension,
                "normalized_value": c.normalized_value,
                "weight": c.weight,
                "weighted_contribution": c.weighted_contribution,
            }
            for c in resp.contributions
        ]
        result_dicts.append(
            {
                "decision": resp.decision,
                "score": resp.score,
                "structural_confidence": resp.structural_confidence,
                "violations": violations,
                "warning": resp.warning,
                "file_path": str(path),
                "percentile": resp.percentile,
                "percentile_available": resp.percentile_available,
                "contributions": contributions,
                "attribution": attribution_to_dict(resp.attribution),
            }
        )

    total = len(result_dicts)
    accepted = sum(1 for r in result_dicts if r["decision"] == "accept")
    warned = sum(1 for r in result_dicts if r["decision"] == "warn")
    rejected = sum(1 for r in result_dicts if r["decision"] == "reject")
    mean_score = sum(r["score"] for r in result_dicts) / total if total else 0.0

    if rejected > 0:
        overall = "reject"
    elif warned > 0:
        overall = "warn"
    else:
        overall = "accept"

    output = {
        "results": result_dicts,
        "summary": {
            "overall_decision": overall,
            "total_files": total,
            "accepted": accepted,
            "warned": warned,
            "rejected": rejected,
            "mean_score": mean_score,
        },
    }
    return json.dumps(output, indent=2)

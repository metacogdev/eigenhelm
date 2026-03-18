"""SARIF 2.1.0 output formatter for eigenhelm evaluation results.

Produces valid SARIF (Static Analysis Results Interchange Format) documents
suitable for upload to GitHub Code Scanning and other SARIF-aware tools.
"""

from __future__ import annotations

import json
from pathlib import Path

from eigenhelm.attribution.serialize import attribution_to_dict
from eigenhelm.helm.models import EvaluationResponse

SARIF_SCHEMA = "https://json.schemastore.org/sarif-2.1.0.json"
SARIF_VERSION = "2.1.0"

# Level mapping: decision -> SARIF level
_DECISION_TO_LEVEL: dict[str, str] = {
    "accept": "note",
    "warn": "warning",
    "reject": "error",
}

# Static rule definitions for eigenhelm
_STATIC_RULES = [
    {
        "id": "eigenhelm/aesthetic-score",
        "name": "AestheticScore",
        "shortDescription": {"text": "Overall aesthetic loss score"},
        "fullDescription": {
            "text": (
                "The overall aesthetic loss score measures code quality against the "
                "eigenhelm aesthetic manifold. Lower scores are better."
            )
        },
        "helpUri": "https://github.com/metacogdev/eigenhelm",
    },
    {
        "id": "eigenhelm/halstead-volume",
        "name": "HalsteadVolume",
        "shortDescription": {"text": "Halstead Volume metric violation"},
        "helpUri": "https://github.com/metacogdev/eigenhelm",
    },
    {
        "id": "eigenhelm/halstead-difficulty",
        "name": "HalsteadDifficulty",
        "shortDescription": {"text": "Halstead Difficulty metric violation"},
        "helpUri": "https://github.com/metacogdev/eigenhelm",
    },
    {
        "id": "eigenhelm/halstead-effort",
        "name": "HalsteadEffort",
        "shortDescription": {"text": "Halstead Effort metric violation"},
        "helpUri": "https://github.com/metacogdev/eigenhelm",
    },
    {
        "id": "eigenhelm/cyclomatic-complexity",
        "name": "CyclomaticComplexity",
        "shortDescription": {"text": "Cyclomatic complexity violation"},
        "helpUri": "https://github.com/metacogdev/eigenhelm",
    },
    {
        "id": "eigenhelm/entropy",
        "name": "ShannonEntropy",
        "shortDescription": {"text": "Shannon entropy metric violation"},
        "helpUri": "https://github.com/metacogdev/eigenhelm",
    },
    {
        "id": "eigenhelm/compression",
        "name": "CompressionRatio",
        "shortDescription": {"text": "Compression ratio (NCD) violation"},
        "helpUri": "https://github.com/metacogdev/eigenhelm",
    },
    {
        "id": "eigenhelm/birkhoff",
        "name": "BirkhoffMeasure",
        "shortDescription": {"text": "Birkhoff aesthetic measure violation"},
        "helpUri": "https://github.com/metacogdev/eigenhelm",
    },
    # 017: Directive rules
    {
        "id": "eigenhelm/directive/reduce_complexity",
        "name": "ReduceComplexity",
        "shortDescription": {"text": "Code complexity exceeds corpus norms"},
        "helpUri": "https://github.com/metacogdev/eigenhelm",
    },
    {
        "id": "eigenhelm/directive/review_token_distribution",
        "name": "ReviewTokenDistribution",
        "shortDescription": {"text": "Unusual byte-level token distribution"},
        "helpUri": "https://github.com/metacogdev/eigenhelm",
    },
    {
        "id": "eigenhelm/directive/extract_repeated_logic",
        "name": "ExtractRepeatedLogic",
        "shortDescription": {"text": "Repeated AST structural patterns detected"},
        "helpUri": "https://github.com/metacogdev/eigenhelm",
    },
    {
        "id": "eigenhelm/directive/review_structure",
        "name": "ReviewStructure",
        "shortDescription": {"text": "Structural deviation from corpus norms"},
        "helpUri": "https://github.com/metacogdev/eigenhelm",
    },
    {
        "id": "eigenhelm/directive/improve_compression",
        "name": "ImproveCompression",
        "shortDescription": {"text": "Low information density indicates redundancy"},
        "helpUri": "https://github.com/metacogdev/eigenhelm",
    },
]


def _violation_rule_id(dimension: str) -> str:
    """Map a violation dimension name to a SARIF rule ID."""
    slug = dimension.lower().replace(" ", "-").replace("_", "-")
    return f"eigenhelm/{slug}"


def build_sarif(
    results: list[tuple[Path | str, EvaluationResponse]],
    tool_version: str,
) -> dict:
    """Build a SARIF 2.1.0 document from evaluation results.

    Args:
        results: List of (file_path, EvaluationResponse) pairs.
        tool_version: Version string for the eigenhelm tool.

    Returns:
        Dict suitable for json.dumps().
    """
    sarif_results = []
    for file_path, resp in results:
        level = _DECISION_TO_LEVEL.get(resp.decision, "note")
        path_str = str(file_path)

        # Build violation details for the message
        violation_parts = []
        for v in resp.critique.violations:
            pct = v.contribution * 100
            violation_parts.append(f"{v.dimension} ({pct:.0f}%)")
        violations_text = (
            "Violations: " + ", ".join(violation_parts) if violation_parts else "No violations."
        )

        # 016: Include percentile in message when available
        if resp.percentile_available and resp.percentile is not None:
            pct = round(resp.percentile)
            score_info = (
                f"Score: {resp.score:.3f} (p{pct} — better than {pct}% of training corpus)"
                f" [{resp.decision}]"
            )
        else:
            score_info = f"Score: {resp.score:.3f} [{resp.decision}]"
        message_text = f"{score_info}. {violations_text}"

        result_entry: dict = {
            "ruleId": "eigenhelm/aesthetic-score",
            "level": level,
            "message": {"text": message_text},
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {"uri": path_str},
                        "region": {"startLine": 1},
                    }
                }
            ],
            "properties": {
                "score": resp.score,
                "decision": resp.decision,
                "structural_confidence": resp.structural_confidence,
                "violations": [
                    {
                        "dimension": v.dimension,
                        "contribution": v.contribution,
                        "raw_value": v.raw_value,
                        "normalized_value": v.normalized_value,
                    }
                    for v in resp.critique.violations
                ],
                "percentile": resp.percentile,
                "percentile_available": resp.percentile_available,
                "contributions": [
                    {
                        "dimension": c.dimension,
                        "normalized_value": c.normalized_value,
                        "weight": c.weight,
                        "weighted_contribution": c.weighted_contribution,
                    }
                    for c in resp.contributions
                ],
                "attribution": attribution_to_dict(resp.attribution),
            },
        }

        # Add related locations for each individual violation
        if resp.critique.violations:
            related = []
            for v in resp.critique.violations:
                related.append(
                    {
                        "message": {
                            "text": (
                                f"{v.dimension}: contribution={v.contribution:.3f}, "
                                f"raw={v.raw_value:.3f}"
                            )
                        },
                        "physicalLocation": {
                            "artifactLocation": {"uri": path_str},
                            "region": {"startLine": 1},
                        },
                    }
                )
            result_entry["relatedLocations"] = related

        sarif_results.append(result_entry)

        # 017: Generate additional SARIF results for each directive
        if resp.attribution is not None:
            for directive in resp.attribution.directives:
                loc = directive.source_location
                directive_entry: dict = {
                    "ruleId": f"eigenhelm/directive/{directive.category}",
                    "level": "warning" if directive.severity != "high" else "error",
                    "message": {
                        "text": (
                            f"[{directive.severity}] {directive.category} "
                            f"({directive.dimension}: {directive.normalized_score:.3f})"
                        ),
                    },
                    "locations": [
                        {
                            "physicalLocation": {
                                "artifactLocation": {
                                    "uri": loc.file_path or path_str,
                                },
                                "region": {
                                    "startLine": loc.start_line,
                                    "endLine": loc.end_line,
                                },
                            }
                        }
                    ],
                }
                sarif_results.append(directive_entry)

    return {
        "version": SARIF_VERSION,
        "$schema": SARIF_SCHEMA,
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "eigenhelm",
                        "version": tool_version,
                        "informationUri": "https://github.com/metacogdev/eigenhelm",
                        "rules": _STATIC_RULES,
                    }
                },
                "results": sarif_results,
                "invocations": [{"executionSuccessful": True}],
            }
        ],
    }


def format_sarif(
    results: list[tuple[Path | str, EvaluationResponse]],
    tool_version: str,
) -> str:
    """Format evaluation results as a SARIF 2.1.0 JSON string.

    Args:
        results: List of (file_path, EvaluationResponse) pairs.
        tool_version: Version string for eigenhelm.

    Returns:
        Pretty-printed JSON string of the SARIF document.
    """
    return json.dumps(build_sarif(results, tool_version), indent=2)

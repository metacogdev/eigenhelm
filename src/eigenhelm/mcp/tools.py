"""MCP tool definitions and execution logic.

Each tool function takes (server_state, arguments) and returns a result dict.
Tool schemas follow the MCP tools/list response format.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from eigenhelm.mcp.server import ServerState

TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "evaluate",
        "description": (
            "Evaluate source code against the eigenhelm aesthetic manifold. "
            "Returns a decision (accept/warn/reject), score, per-dimension "
            "contributions, and actionable directives."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "description": "Source code to evaluate.",
                },
                "language": {
                    "type": "string",
                    "description": "Language key (python, javascript, typescript, go, rust).",
                },
                "file_path": {
                    "type": "string",
                    "description": "Optional file path for context in directives.",
                },
                "top_n": {
                    "type": "integer",
                    "description": "Top features per PCA dimension in attribution (default 3).",
                    "default": 3,
                },
                "directive_threshold": {
                    "type": "number",
                    "description": "Minimum normalized score to generate directives (default 0.3).",
                    "default": 0.3,
                },
            },
            "required": ["source", "language"],
        },
    },
    {
        "name": "evaluate_batch",
        "description": (
            "Evaluate multiple source files in a single call. Returns per-file "
            "results and an aggregate summary with overall decision and mean score."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "files": {
                    "type": "array",
                    "description": "List of files to evaluate.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "source": {"type": "string"},
                            "language": {"type": "string"},
                            "file_path": {"type": "string"},
                            "top_n": {"type": "integer", "default": 3},
                            "directive_threshold": {
                                "type": "number",
                                "default": 0.3,
                            },
                        },
                        "required": ["source", "language"],
                    },
                },
            },
            "required": ["files"],
        },
    },
    {
        "name": "model_list",
        "description": (
            "List available eigenhelm models. Shows locally installed models "
            "by default, or remote registry models with include_remote=true."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "include_remote": {
                    "type": "boolean",
                    "description": "Also fetch models from the remote registry.",
                    "default": False,
                },
            },
        },
    },
    {
        "name": "model_info",
        "description": (
            "Get detailed metadata for a specific model including version, "
            "component count, calibrated thresholds, and score distribution."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Model name (without .npz extension).",
                },
            },
            "required": ["name"],
        },
    },
    {
        "name": "model_switch",
        "description": (
            "Switch the active model used for evaluation. Resolves locally "
            "first; pulls from the remote registry if not found. Use model_list "
            "to see available models."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Model name to activate.",
                },
            },
            "required": ["name"],
        },
    },
]

TOOL_MAP: dict[str, dict[str, Any]] = {t["name"]: t for t in TOOL_DEFINITIONS}


def execute_evaluate(state: ServerState, args: dict[str, Any]) -> list[dict[str, Any]]:
    """Execute the evaluate tool."""
    from eigenhelm.helm.models import EvaluationRequest

    source = args["source"]
    language = args["language"]

    request = EvaluationRequest(
        source=source,
        language=language,
        file_path=args.get("file_path"),
        top_n=args.get("top_n", 3),
        directive_threshold=args.get("directive_threshold", 0.3),
    )
    response = state.helm.evaluate(request)
    return [
        {"type": "text", "text": _format_evaluation(response, args.get("file_path"))}
    ]


def execute_evaluate_batch(
    state: ServerState, args: dict[str, Any]
) -> list[dict[str, Any]]:
    """Execute the evaluate_batch tool."""
    import json

    from eigenhelm.helm.models import EvaluationRequest

    files = args["files"]
    results = []
    for entry in files:
        request = EvaluationRequest(
            source=entry["source"],
            language=entry["language"],
            file_path=entry.get("file_path"),
            top_n=entry.get("top_n", 3),
            directive_threshold=entry.get("directive_threshold", 0.3),
        )
        response = state.helm.evaluate(request)
        results.append(_response_to_dict(response, entry.get("file_path")))

    # Compute summary
    total = len(results)
    if total == 0:
        summary = {"overall_decision": "accept", "total_files": 0}
    else:
        accepted = sum(1 for r in results if r["decision"] == "accept")
        warned = sum(1 for r in results if r["decision"] == "warn")
        rejected = sum(1 for r in results if r["decision"] == "reject")
        mean_score = sum(r["score"] for r in results) / total

        if rejected > 0:
            overall = "reject"
        elif warned > 0:
            overall = "warn"
        else:
            overall = "accept"

        summary = {
            "overall_decision": overall,
            "total_files": total,
            "accepted": accepted,
            "warned": warned,
            "rejected": rejected,
            "mean_score": round(mean_score, 4),
        }

    output = {"results": results, "summary": summary}
    return [{"type": "text", "text": json.dumps(output, indent=2)}]


def execute_model_list(
    state: ServerState, args: dict[str, Any]
) -> list[dict[str, Any]]:
    """Execute the model_list tool."""
    import json

    from eigenhelm.registry import list_local

    models = []
    for m in list_local():
        entry = {
            "name": m.name,
            "source": "bundled" if m.bundled else "cached",
            "path": m.path,
        }
        if state.active_model_name and m.name == state.active_model_name:
            entry["active"] = True
        models.append(entry)

    if args.get("include_remote"):
        try:
            from eigenhelm.registry import list_remote

            remote = list_remote()
            remote_names = {m.name for m in list_local()}
            for m in remote:
                if m.name not in remote_names:
                    models.append(
                        {
                            "name": m.name,
                            "source": "remote",
                            "language": m.language,
                            "corpus_class": m.corpus_class,
                            "n_components": m.n_components,
                        }
                    )
        except Exception as exc:
            models.append({"error": f"Failed to fetch remote registry: {exc}"})

    return [{"type": "text", "text": json.dumps(models, indent=2)}]


def execute_model_info(
    state: ServerState, args: dict[str, Any]
) -> list[dict[str, Any]]:
    """Execute the model_info tool."""
    import json

    from eigenhelm.eigenspace import load_model
    from eigenhelm.registry import resolve_model

    name = args["name"]
    path = resolve_model(name)
    if path is None:
        return [
            {
                "type": "text",
                "text": f"Model '{name}' not found locally. Try model_switch to pull it.",
            }
        ]

    m = load_model(path)
    info: dict[str, Any] = {
        "name": name,
        "path": str(path),
        "version": m.version,
        "n_components": m.n_components,
        "corpus_hash": m.corpus_hash,
    }
    if m.language:
        info["language"] = m.language
    if m.corpus_class:
        info["corpus_class"] = m.corpus_class
    if m.n_training_files:
        info["n_training_files"] = m.n_training_files
    if m.calibrated_accept is not None:
        info["calibrated_accept"] = round(m.calibrated_accept, 4)
    if m.calibrated_reject is not None:
        info["calibrated_reject"] = round(m.calibrated_reject, 4)
    if m.score_distribution:
        d = m.score_distribution
        info["score_distribution"] = {
            "min": round(d.min, 4),
            "p10": round(d.p10, 4),
            "p25": round(d.p25, 4),
            "median": round(d.median, 4),
            "p75": round(d.p75, 4),
            "p90": round(d.p90, 4),
            "max": round(d.max, 4),
        }
    if state.active_model_name == name:
        info["active"] = True

    return [{"type": "text", "text": json.dumps(info, indent=2)}]


def execute_model_switch(
    state: ServerState, args: dict[str, Any]
) -> list[dict[str, Any]]:
    """Execute the model_switch tool."""
    from eigenhelm.eigenspace import load_model
    from eigenhelm.helm import DynamicHelm
    from eigenhelm.registry import pull_model, resolve_model

    name = args["name"]

    # Try local first
    path = resolve_model(name)
    if path is None:
        # Pull from registry
        try:
            path = pull_model(name)
        except Exception as exc:
            return [
                {"type": "text", "text": f"Failed to resolve model '{name}': {exc}"}
            ]

    eigenspace = load_model(path)
    state.helm = DynamicHelm(eigenspace=eigenspace)
    state.active_model_name = name

    info = f"Switched to model '{name}' ({eigenspace.n_components} components"
    if eigenspace.language:
        info += f", {eigenspace.language}"
    info += ")"
    return [{"type": "text", "text": info}]


TOOL_HANDLERS = {
    "evaluate": execute_evaluate,
    "evaluate_batch": execute_evaluate_batch,
    "model_list": execute_model_list,
    "model_info": execute_model_info,
    "model_switch": execute_model_switch,
}


def _response_to_dict(response, file_path: str | None = None) -> dict[str, Any]:
    """Convert an EvaluationResponse to a serializable dict."""
    result: dict[str, Any] = {
        "decision": response.decision,
        "score": round(response.score, 4),
        "structural_confidence": response.structural_confidence,
    }
    if file_path:
        result["file_path"] = file_path
    if response.percentile_available and response.percentile is not None:
        result["percentile"] = round(response.percentile, 1)
    if response.warning:
        result["warning"] = response.warning

    # Contributions
    if response.contributions:
        result["contributions"] = [
            {
                "dimension": c.dimension,
                "normalized_value": round(c.normalized_value, 4),
                "weight": round(c.weight, 4),
                "weighted_contribution": round(c.weighted_contribution, 4),
            }
            for c in response.contributions
        ]

    # Directives (most actionable part of attribution)
    if response.attribution and response.attribution.directives:
        result["directives"] = [
            {
                "category": d.category,
                "dimension": d.dimension,
                "severity": d.severity,
                "location": {
                    "code_unit_name": d.source_location.code_unit_name,
                    "start_line": d.source_location.start_line,
                    "end_line": d.source_location.end_line,
                },
                "top_feature": {
                    "name": d.attribution.features[0].feature_name,
                    "contribution": round(
                        d.attribution.features[0].contribution_value, 4
                    ),
                    "deviation_sigma": round(
                        d.attribution.features[0].standardized_deviation, 2
                    ),
                }
                if d.attribution.features
                else None,
            }
            for d in response.attribution.directives
        ]

    # Declaration ratio
    if response.declaration_ratio is not None:
        result["declaration_ratio"] = round(response.declaration_ratio, 4)

    return result


def _format_evaluation(response, file_path: str | None = None) -> str:
    """Format a single evaluation as JSON text."""
    import json

    return json.dumps(_response_to_dict(response, file_path), indent=2)

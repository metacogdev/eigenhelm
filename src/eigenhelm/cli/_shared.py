from eigenhelm.helm.models import EvaluationResponse


def _apply_thresholds(
    response: EvaluationResponse,
    thresholds,
    cli_accept: float | None = None,
    cli_reject: float | None = None,
    model_accept: float | None = None,
    model_reject: float | None = None,
) -> EvaluationResponse:
    """Re-derive decision from score using the full effective threshold hierarchy.

    Hierarchy: CLI flag > Path config > Global config > Model calibration > Hardcoded defaults.
    """
    from dataclasses import replace

    # Resolve full effective pair
    accept = (
        cli_accept
        if cli_accept is not None
        else (
            thresholds.accept
            if thresholds and thresholds.accept is not None
            else model_accept
        )
    )
    reject = (
        cli_reject
        if cli_reject is not None
        else (
            thresholds.reject
            if thresholds and thresholds.reject is not None
            else model_reject
        )
    )

    # Fallback to hardcoded if model didn't provide them
    if accept is None:
        accept = 0.4
    if reject is None:
        reject = 0.6

    if accept >= reject:
        raise ValueError(
            f"Effective thresholds are invalid: accept ({accept}) must be less than reject ({reject}). "
            "This can happen if a CLI override conflicts with a config file threshold."
        )

    score = response.score

    if score > reject:
        new_decision = "reject"
    elif score < accept:
        new_decision = "accept"
    else:
        new_decision = "warn"

    if new_decision == response.decision:
        return response
    return replace(response, decision=new_decision)


def format_score_distribution(sd, precision: int = 3) -> str:
    """Format CalibrationStats score distribution consistently across the CLI."""
    fmt = f".{precision}f"

    def _get(k):
        return sd[k] if isinstance(sd, dict) else getattr(sd, k)

    return (
        f"min={_get('min'):{fmt}}  p10={_get('p10'):{fmt}}  "
        f"p25={_get('p25'):{fmt}}  median={_get('median'):{fmt}}  "
        f"p75={_get('p75'):{fmt}}  p90={_get('p90'):{fmt}}  max={_get('max'):{fmt}}"
    )

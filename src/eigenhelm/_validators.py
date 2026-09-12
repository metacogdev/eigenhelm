def _validate_unit_interval(name: str, value: float) -> None:
    """Validate that a value is in [0.0, 1.0]."""
    if not (0.0 <= value <= 1.0):
        raise ValueError(f"{name} must be in [0.0, 1.0], got {value}")


def _validate_ordered(name1: str, value1: float, name2: str, value2: float) -> None:
    """Validate that value1 <= value2."""
    if value1 > value2:
        raise ValueError(f"Values must be ordered: {name1}={value1} > {name2}={value2}")

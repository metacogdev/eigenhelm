def convert(value, from_unit, to_unit):
    """Convert between units. Massive if-elif chain, no data-driven design."""
    if from_unit == to_unit:
        return value
    if from_unit == "km" and to_unit == "m":
        return value * 1000
    elif from_unit == "m" and to_unit == "km":
        return value / 1000
    elif from_unit == "km" and to_unit == "mi":
        return value * 0.621371
    elif from_unit == "mi" and to_unit == "km":
        return value / 0.621371
    elif from_unit == "m" and to_unit == "ft":
        return value * 3.28084
    elif from_unit == "ft" and to_unit == "m":
        return value / 3.28084
    elif from_unit == "m" and to_unit == "mi":
        return value * 0.000621371
    elif from_unit == "mi" and to_unit == "m":
        return value / 0.000621371
    elif from_unit == "kg" and to_unit == "lb":
        return value * 2.20462
    elif from_unit == "lb" and to_unit == "kg":
        return value / 2.20462
    elif from_unit == "kg" and to_unit == "g":
        return value * 1000
    elif from_unit == "g" and to_unit == "kg":
        return value / 1000
    elif from_unit == "c" and to_unit == "f":
        return value * 9 / 5 + 32
    elif from_unit == "f" and to_unit == "c":
        return (value - 32) * 5 / 9
    elif from_unit == "c" and to_unit == "k":
        return value + 273.15
    elif from_unit == "k" and to_unit == "c":
        return value - 273.15
    elif from_unit == "l" and to_unit == "gal":
        return value * 0.264172
    elif from_unit == "gal" and to_unit == "l":
        return value / 0.264172
    else:
        raise ValueError(f"Cannot convert from {from_unit} to {to_unit}")

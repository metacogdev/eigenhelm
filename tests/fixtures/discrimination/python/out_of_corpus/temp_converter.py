def celsius_to_fahrenheit(c):
    f = c * 9 / 5 + 32
    return f


def fahrenheit_to_celsius(f):
    c = (f - 32) * 5 / 9
    return c


def print_conversion(value, unit):
    if unit == "C":
        result = celsius_to_fahrenheit(value)
        print(str(value) + "C = " + str(result) + "F")
    elif unit == "F":
        result = fahrenheit_to_celsius(value)
        print(str(value) + "F = " + str(result) + "C")
    else:
        print("Unknown unit")

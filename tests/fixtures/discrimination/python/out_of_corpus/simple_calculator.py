def add(a, b):
    result = a + b
    return result


def subtract(a, b):
    result = a - b
    return result


def multiply(a, b):
    result = a * b
    return result


def divide(a, b):
    if b == 0:
        print("Error: cannot divide by zero")
        return None
    result = a / b
    return result

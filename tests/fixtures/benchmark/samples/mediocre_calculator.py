def calculate(expression):
    """Evaluate simple math expression string. Fragile and limited."""
    expression = expression.strip()
    result = 0

    # Try to find operator
    op = None
    op_pos = -1
    for i, c in enumerate(expression):
        if i > 0 and c in "+-*/" and expression[i - 1] != "e":
            op = c
            op_pos = i
            break

    if op is None:
        try:
            return float(expression)
        except ValueError:
            return None

    left = expression[:op_pos].strip()
    right = expression[op_pos + 1 :].strip()

    try:
        a = float(left)
        b = float(right)
    except ValueError:
        return None

    if op == "+":
        result = a + b
    elif op == "-":
        result = a - b
    elif op == "*":
        result = a * b
    elif op == "/":
        if b != 0:
            result = a / b
        else:
            return None

    return result

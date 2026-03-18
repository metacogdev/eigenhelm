def fibonacci(n):
    """Return the nth Fibonacci number using iteration."""
    if n <= 0:
        return 0
    if n == 1:
        return 1
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b


def fibonacci_sequence(count):
    """Generate the first count Fibonacci numbers."""
    result = []
    for i in range(count):
        result.append(fibonacci(i))
    return result

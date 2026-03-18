def fibonacci(n):
    """Compute nth Fibonacci number iteratively.

    Uses O(1) space with two-variable iteration.
    Time: O(n). Space: O(1).
    """
    if n <= 0:
        return 0
    if n == 1:
        return 1
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b

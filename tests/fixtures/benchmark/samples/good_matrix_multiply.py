def matrix_multiply(a, b):
    """Multiply two matrices using nested loops.

    Simple O(n³) implementation. Not optimized but correct.
    """
    rows_a = len(a)
    cols_a = len(a[0])
    cols_b = len(b[0])
    result = [[0] * cols_b for _ in range(rows_a)]
    for i in range(rows_a):
        for j in range(cols_b):
            for k in range(cols_a):
                result[i][j] += a[i][k] * b[k][j]
    return result

import time
from contextlib import contextmanager


@contextmanager
def timer(label="operation"):
    """Context manager that measures and prints elapsed time.

    Usage:
        with timer("sorting"):
            data.sort()
        # Prints: sorting took 0.0023s
    """
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        print(f"{label} took {elapsed:.4f}s")

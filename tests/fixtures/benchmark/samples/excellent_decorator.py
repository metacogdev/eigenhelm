import functools
import time


def retry(max_attempts=3, delay=0.1):
    """Decorator that retries a function on exception.

    Args:
        max_attempts: Maximum number of attempts before re-raising.
        delay: Seconds to wait between attempts.

    Returns:
        Decorated function that retries on failure.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    last_exc = exc
                    if attempt < max_attempts - 1:
                        time.sleep(delay)
            raise last_exc
        return wrapper
    return decorator

import time


class TokenBucket:
    """Token bucket rate limiter.

    Allows bursts up to capacity, then refills at a steady rate.
    """

    def __init__(self, rate, capacity):
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_refill = time.monotonic()

    def _refill(self):
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last_refill = now

    def consume(self, n=1):
        """Try to consume n tokens. Returns True if allowed."""
        self._refill()
        if self.tokens >= n:
            self.tokens -= n
            return True
        return False

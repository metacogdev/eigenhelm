class RingBuffer:
    """Fixed-size circular buffer. Overwrites oldest data when full."""

    def __init__(self, capacity):
        self.capacity = capacity
        self._buffer = [None] * capacity
        self._head = 0
        self._count = 0

    def append(self, item):
        """Add item, overwriting oldest if full."""
        idx = (self._head + self._count) % self.capacity
        if self._count == self.capacity:
            self._head = (self._head + 1) % self.capacity
        else:
            self._count += 1
        self._buffer[idx] = item

    def __getitem__(self, index):
        if index < 0 or index >= self._count:
            raise IndexError("ring buffer index out of range")
        return self._buffer[(self._head + index) % self.capacity]

    def __len__(self):
        return self._count

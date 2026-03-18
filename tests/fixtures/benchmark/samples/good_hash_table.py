class SimpleHashTable:
    """Hash table with separate chaining for collision resolution."""

    def __init__(self, capacity=16):
        self.capacity = capacity
        self.size = 0
        self.buckets = [[] for _ in range(capacity)]

    def _hash(self, key):
        return hash(key) % self.capacity

    def put(self, key, value):
        """Insert or update a key-value pair."""
        idx = self._hash(key)
        for i, (k, v) in enumerate(self.buckets[idx]):
            if k == key:
                self.buckets[idx][i] = (key, value)
                return
        self.buckets[idx].append((key, value))
        self.size += 1

    def get(self, key, default=None):
        """Retrieve value by key, returning default if not found."""
        idx = self._hash(key)
        for k, v in self.buckets[idx]:
            if k == key:
                return v
        return default

    def delete(self, key):
        """Remove key from table. Returns True if found."""
        idx = self._hash(key)
        for i, (k, v) in enumerate(self.buckets[idx]):
            if k == key:
                self.buckets[idx].pop(i)
                self.size -= 1
                return True
        return False

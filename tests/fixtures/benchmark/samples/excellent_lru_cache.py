from collections import OrderedDict


class LRUCache:
    """Least Recently Used cache with O(1) get and put.

    Uses OrderedDict for combined hash map + doubly linked list.
    Capacity is fixed at construction time.
    """

    def __init__(self, capacity: int) -> None:
        self.capacity = capacity
        self._store: OrderedDict[str, object] = OrderedDict()

    def get(self, key: str) -> object | None:
        """Return value for key, marking it as recently used."""
        if key not in self._store:
            return None
        self._store.move_to_end(key)
        return self._store[key]

    def put(self, key: str, value: object) -> None:
        """Insert or update key-value pair, evicting LRU if at capacity."""
        if key in self._store:
            self._store.move_to_end(key)
        self._store[key] = value
        if len(self._store) > self.capacity:
            self._store.popitem(last=False)

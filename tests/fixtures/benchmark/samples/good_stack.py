class Stack:
    """LIFO stack backed by a Python list.

    All operations are O(1) amortized.
    """

    def __init__(self):
        self._items = []

    def push(self, item):
        """Add item to top of stack."""
        self._items.append(item)

    def pop(self):
        """Remove and return top item. Raises IndexError if empty."""
        if self.is_empty():
            raise IndexError("pop from empty stack")
        return self._items.pop()

    def peek(self):
        """Return top item without removing. Raises IndexError if empty."""
        if self.is_empty():
            raise IndexError("peek at empty stack")
        return self._items[-1]

    def is_empty(self):
        return len(self._items) == 0

    def __len__(self):
        return len(self._items)

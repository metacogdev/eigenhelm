class SimpleQueue:
    def __init__(self):
        self.items = []

    def enqueue(self, item):
        self.items.append(item)

    def dequeue(self):
        if len(self.items) == 0:
            return None
        return self.items.pop(0)

    def front(self):
        if len(self.items) == 0:
            return None
        return self.items[0]

    def is_empty(self):
        return len(self.items) == 0

    def size(self):
        return len(self.items)


def rotate_list(lst, k):
    if len(lst) == 0:
        return lst
    k = k % len(lst)
    return lst[k:] + lst[:k]


def flatten_list(nested):
    result = []
    for item in nested:
        if isinstance(item, list):
            result.extend(flatten_list(item))
        else:
            result.append(item)
    return result

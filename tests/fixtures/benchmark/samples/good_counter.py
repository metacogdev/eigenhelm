def most_frequent(items, n=1):
    """Return the n most frequent items with their counts.

    Uses a simple counting approach without collections.Counter.

    >>> most_frequent(['a', 'b', 'a', 'c', 'a', 'b'], 2)
    [('a', 3), ('b', 2)]
    """
    counts = {}
    for item in items:
        counts[item] = counts.get(item, 0) + 1

    sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    return sorted_items[:n]

def chunked(iterable, size):
    """Yield successive chunks of given size from iterable.

    Final chunk may be smaller than size.
    Time: O(n). Space: O(size) per chunk.

    >>> list(chunked([1, 2, 3, 4, 5], 2))
    [[1, 2], [3, 4], [5]]
    """
    chunk = []
    for item in iterable:
        chunk.append(item)
        if len(chunk) == size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk

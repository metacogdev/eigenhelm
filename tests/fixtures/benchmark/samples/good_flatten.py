def flatten(nested):
    """Flatten arbitrarily nested lists into a single list.

    Handles any depth of nesting. Non-list items are yielded as-is.

    >>> list(flatten([1, [2, [3, 4], 5], 6]))
    [1, 2, 3, 4, 5, 6]
    """
    for item in nested:
        if isinstance(item, list):
            yield from flatten(item)
        else:
            yield item

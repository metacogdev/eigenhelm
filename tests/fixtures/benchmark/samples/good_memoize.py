def memoize(func):
    """Simple memoization decorator using a dict cache.

    Only works with hashable arguments.
    """
    cache = {}

    def wrapper(*args):
        if args not in cache:
            cache[args] = func(*args)
        return cache[args]

    wrapper.cache = cache
    wrapper.__wrapped__ = func
    return wrapper


@memoize
def edit_distance(s1, s2):
    """Compute Levenshtein edit distance between two strings."""
    if not s1:
        return len(s2)
    if not s2:
        return len(s1)
    if s1[0] == s2[0]:
        return edit_distance(s1[1:], s2[1:])
    return 1 + min(
        edit_distance(s1[1:], s2),
        edit_distance(s1, s2[1:]),
        edit_distance(s1[1:], s2[1:]),
    )

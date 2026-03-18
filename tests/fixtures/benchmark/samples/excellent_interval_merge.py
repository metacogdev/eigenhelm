def merge_intervals(intervals):
    """Merge overlapping intervals.

    Args:
        intervals: List of (start, end) tuples.

    Returns:
        List of merged (start, end) tuples, sorted by start.
        Time: O(n log n). Space: O(n).

    >>> merge_intervals([(1, 3), (2, 6), (8, 10), (15, 18)])
    [(1, 6), (8, 10), (15, 18)]
    """
    if not intervals:
        return []

    sorted_intervals = sorted(intervals, key=lambda x: x[0])
    merged = [sorted_intervals[0]]

    for start, end in sorted_intervals[1:]:
        prev_start, prev_end = merged[-1]
        if start <= prev_end:
            merged[-1] = (prev_start, max(prev_end, end))
        else:
            merged.append((start, end))

    return merged

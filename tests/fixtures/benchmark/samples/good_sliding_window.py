def max_subarray_sum(arr, k):
    """Find maximum sum of contiguous subarray of length k.

    Uses sliding window technique.
    Time: O(n). Space: O(1).
    """
    if not arr or k <= 0 or k > len(arr):
        return 0

    window_sum = sum(arr[:k])
    max_sum = window_sum

    for i in range(k, len(arr)):
        window_sum += arr[i] - arr[i - k]
        max_sum = max(max_sum, window_sum)

    return max_sum

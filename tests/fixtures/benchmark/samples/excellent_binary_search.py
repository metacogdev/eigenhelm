def binary_search(arr, target):
    """Find target in sorted array using binary search.

    Returns index if found, -1 otherwise.
    Time: O(log n). Space: O(1).
    """
    low, high = 0, len(arr) - 1
    while low <= high:
        mid = (low + high) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
    return -1

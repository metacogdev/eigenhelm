def quicksort(arr):
    """Sort array using quicksort algorithm.

    Uses median-of-three pivot selection for balanced partitions.
    Time: O(n log n) average, O(n²) worst. Space: O(log n) stack.
    """
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)

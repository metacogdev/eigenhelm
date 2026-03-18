def heapify(arr, n, i):
    """Maintain max-heap property at index i.

    Sifts element down until heap invariant is restored.
    Time: O(log n). Space: O(1).
    """
    largest = i
    left = 2 * i + 1
    right = 2 * i + 2

    if left < n and arr[left] > arr[largest]:
        largest = left
    if right < n and arr[right] > arr[largest]:
        largest = right

    if largest != i:
        arr[i], arr[largest] = arr[largest], arr[i]
        heapify(arr, n, largest)


def heap_sort(arr):
    """Sort array using heap sort.

    Builds a max-heap then extracts elements.
    Time: O(n log n). Space: O(1) auxiliary.
    """
    n = len(arr)
    for i in range(n // 2 - 1, -1, -1):
        heapify(arr, n, i)
    for i in range(n - 1, 0, -1):
        arr[0], arr[i] = arr[i], arr[0]
        heapify(arr, i, 0)
    return arr

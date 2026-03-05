fn quicksort(arr: &mut Vec<i64>) {
    let len = arr.len();
    if len <= 1 {
        return;
    }
    quicksort_range(arr, 0, len - 1);
}

fn quicksort_range(arr: &mut Vec<i64>, low: usize, high: usize) {
    if low < high {
        let pivot_idx = partition(arr, low, high);
        if pivot_idx > 0 {
            quicksort_range(arr, low, pivot_idx - 1);
        }
        quicksort_range(arr, pivot_idx + 1, high);
    }
}

fn partition(arr: &mut Vec<i64>, low: usize, high: usize) -> usize {
    let pivot = arr[high];
    let mut i = low;
    for j in low..high {
        if arr[j] <= pivot {
            arr.swap(i, j);
            i += 1;
        }
    }
    arr.swap(i, high);
    i
}

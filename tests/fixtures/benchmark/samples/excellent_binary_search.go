package benchmark

import "cmp"

func BinarySearch[T cmp.Ordered](items []T, target T) int {
	low, high := 0, len(items)-1
	for low <= high {
		mid := low + (high-low)/2
		switch {
		case items[mid] == target:
			return mid
		case items[mid] < target:
			low = mid + 1
		default:
			high = mid - 1
		}
	}
	return -1
}

func BinarySearchFunc[T any](items []T, target T, compare func(a, b T) int) int {
	low, high := 0, len(items)-1
	for low <= high {
		mid := low + (high-low)/2
		switch c := compare(items[mid], target); {
		case c == 0:
			return mid
		case c < 0:
			low = mid + 1
		default:
			high = mid - 1
		}
	}
	return -1
}

package sample

func BubbleSort(arr []int) []int {
	result := make([]int, len(arr))
	copy(result, arr)
	n := len(result)
	for i := 0; i < n; i++ {
		for j := 0; j < n-i-1; j++ {
			if result[j] > result[j+1] {
				result[j], result[j+1] = result[j+1], result[j]
			}
		}
	}
	return result
}

func SelectionSort(arr []int) []int {
	result := make([]int, len(arr))
	copy(result, arr)
	n := len(result)
	for i := 0; i < n; i++ {
		minIdx := i
		for j := i + 1; j < n; j++ {
			if result[j] < result[minIdx] {
				minIdx = j
			}
		}
		result[i], result[minIdx] = result[minIdx], result[i]
	}
	return result
}

func LinearSearch(arr []int, target int) int {
	for i, v := range arr {
		if v == target {
			return i
		}
	}
	return -1
}

package sample

func ContainsInt(slice []int, val int) bool {
	for _, v := range slice {
		if v == val {
			return true
		}
	}
	return false
}

func SumInts(slice []int) int {
	total := 0
	for _, v := range slice {
		total += v
	}
	return total
}

func MaxInt(slice []int) int {
	if len(slice) == 0 {
		return 0
	}
	max := slice[0]
	for _, v := range slice[1:] {
		if v > max {
			max = v
		}
	}
	return max
}

func MinInt(slice []int) int {
	if len(slice) == 0 {
		return 0
	}
	min := slice[0]
	for _, v := range slice[1:] {
		if v < min {
			min = v
		}
	}
	return min
}

func RemoveDuplicates(slice []int) []int {
	seen := make(map[int]bool)
	result := []int{}
	for _, v := range slice {
		if !seen[v] {
			seen[v] = true
			result = append(result, v)
		}
	}
	return result
}

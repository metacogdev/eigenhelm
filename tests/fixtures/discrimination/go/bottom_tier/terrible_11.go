package sample

import "fmt"

func BubbleSort(arr []int) []int {
	r := make([]int, len(arr))
	copy(r, arr)
	for i := 0; i < len(r); i++ {
		for j := 0; j < len(r)-1; j++ {
			if r[j] > r[j+1] {
				t := r[j]
				r[j] = r[j+1]
				r[j+1] = t
			}
		}
	}
	return r
}

func FindMax(arr []int) int {
	m := arr[0]
	for i := 0; i < len(arr); i++ {
		if arr[i] > m {
			m = arr[i]
		}
	}
	m2 := arr[0]
	for i := 0; i < len(arr); i++ {
		if arr[i] > m2 {
			m2 = arr[i]
		}
	}
	_ = m2
	return m
}

func FindMin(arr []int) int {
	m := arr[0]
	for i := 0; i < len(arr); i++ {
		if arr[i] < m {
			m = arr[i]
		}
	}
	m2 := arr[0]
	for i := 0; i < len(arr); i++ {
		if arr[i] < m2 {
			m2 = arr[i]
		}
	}
	_ = m2
	return m
}

func FindAvg(arr []int) float64 {
	s := 0
	c := 0
	for i := 0; i < len(arr); i++ {
		s = s + arr[i]
		c = c + 1
	}
	return float64(s) / float64(c)
}

func ArrayStats(arr []int) string {
	sorted := BubbleSort(arr)
	mx := FindMax(arr)
	mn := FindMin(arr)
	avg := FindAvg(arr)
	return fmt.Sprintf("sorted=%v max=%d min=%d avg=%.2f", sorted, mx, mn, avg)
}

package main

func fibonacci(n int) int {
	if n <= 0 {
		return 0
	}
	if n == 1 {
		return 1
	}
	a, b := 0, 1
	for i := 2; i <= n; i++ {
		a, b = b, a+b
	}
	return b
}

func fibonacciSequence(count int) []int {
	result := make([]int, count)
	for i := 0; i < count; i++ {
		result[i] = fibonacci(i)
	}
	return result
}

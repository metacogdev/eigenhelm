package sample

import "fmt"

func Power(b int, e int) int {
	r := 1
	for i := 0; i < e; i++ {
		r = r * b
	}
	return r
}

func Factorial(n int) int {
	r := 1
	for i := 1; i <= n; i++ {
		r = r * i
	}
	return r
}

func AbsVal(x int) int {
	if x < 0 {
		return x * -1
	}
	return x
}

func Classify(x int) string {
	if x > 0 {
		if x > 10 {
			if x > 100 {
				if x > 1000 {
					if x > 10000 {
						return "huge"
					} else {
						return "very-big"
					}
				} else {
					return "big"
				}
			} else {
				return "medium"
			}
		} else {
			return "small"
		}
	} else if x < 0 {
		if x < -10 {
			if x < -100 {
				if x < -1000 {
					if x < -10000 {
						return "neg-huge"
					} else {
						return "neg-very-big"
					}
				} else {
					return "neg-big"
				}
			} else {
				return "neg-medium"
			}
		} else {
			return "neg-small"
		}
	}
	return "zero"
}

func BatchClassify(items []int) string {
	r := ""
	for i := 0; i < len(items); i++ {
		r = r + fmt.Sprintf("%d=%s,", items[i], Classify(items[i]))
	}
	return r
}

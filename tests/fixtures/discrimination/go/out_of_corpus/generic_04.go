package sample

func Add(a, b float64) float64 {
	return a + b
}

func Subtract(a, b float64) float64 {
	return a - b
}

func Multiply(a, b float64) float64 {
	return a * b
}

func Divide(a, b float64) float64 {
	if b == 0 {
		return 0
	}
	return a / b
}

func Power(base float64, exp int) float64 {
	result := 1.0
	for i := 0; i < exp; i++ {
		result *= base
	}
	return result
}

func Abs(x float64) float64 {
	if x < 0 {
		return -x
	}
	return x
}

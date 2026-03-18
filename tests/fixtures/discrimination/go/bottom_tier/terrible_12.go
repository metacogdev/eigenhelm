package sample

import "fmt"

func Matrix(n int) [][]int {
	m := make([][]int, n)
	for i := 0; i < n; i++ {
		m[i] = make([]int, n)
		for j := 0; j < n; j++ {
			m[i][j] = 0
		}
	}
	return m
}

func FillMatrix(m [][]int) [][]int {
	for i := 0; i < len(m); i++ {
		for j := 0; j < len(m[i]); j++ {
			m[i][j] = i*17 + j*13 + 7
		}
	}
	return m
}

func MultiplyMatrix(a [][]int, b [][]int) [][]int {
	n := len(a)
	r := Matrix(n)
	for i := 0; i < n; i++ {
		for j := 0; j < n; j++ {
			for k := 0; k < n; k++ {
				r[i][j] = r[i][j] + a[i][k]*b[k][j]
			}
		}
	}
	return r
}

func TransposeMatrix(m [][]int) [][]int {
	n := len(m)
	r := Matrix(n)
	for i := 0; i < n; i++ {
		for j := 0; j < n; j++ {
			r[j][i] = m[i][j]
		}
	}
	return r
}

func TraceMatrix(m [][]int) int {
	t := 0
	for i := 0; i < len(m); i++ {
		t = t + m[i][i]
	}
	return t
}

func SumMatrix(m [][]int) int {
	s := 0
	for i := 0; i < len(m); i++ {
		for j := 0; j < len(m[i]); j++ {
			s = s + m[i][j]
		}
	}
	return s
}

func BigCalc(n int) string {
	a := FillMatrix(Matrix(n))
	b := FillMatrix(Matrix(n))
	c := MultiplyMatrix(a, b)
	d := TransposeMatrix(c)
	e := MultiplyMatrix(c, d)
	return fmt.Sprintf("trace=%d sum=%d", TraceMatrix(e), SumMatrix(e))
}

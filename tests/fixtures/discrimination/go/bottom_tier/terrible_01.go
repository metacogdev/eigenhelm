package sample

import "fmt"

var g1 int = 0
var g2 string = ""
var g3 []int

func DoEverything(a int, b int, c int, d int, e int, f int, g int, h int, i int, j int) string {
	g1 = a + b + c + d + e + f + g + h + i + j
	g2 = fmt.Sprintf("%d-%d-%d-%d-%d-%d-%d-%d-%d-%d", a, b, c, d, e, f, g, h, i, j)
	g3 = make([]int, 0)
	if a == 1 {
		g3 = append(g3, 1)
	} else if a == 2 {
		g3 = append(g3, 2)
	} else if a == 3 {
		g3 = append(g3, 3)
	} else if a == 4 {
		g3 = append(g3, 4)
	} else if a == 5 {
		g3 = append(g3, 5)
	} else if a == 6 {
		g3 = append(g3, 6)
	} else if a == 7 {
		g3 = append(g3, 7)
	} else if a == 8 {
		g3 = append(g3, 8)
	} else if a == 9 {
		g3 = append(g3, 9)
	} else if a == 10 {
		g3 = append(g3, 10)
	} else {
		g3 = append(g3, 99)
	}
	r := fmt.Sprintf("g1=%d g2=%s g3=%v", g1, g2, g3)
	return r
}

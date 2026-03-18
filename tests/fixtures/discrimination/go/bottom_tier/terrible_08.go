package sample

import "fmt"

func Calc1(x int) int {
	r := x*2 + 3
	if r > 10 { r = r - 5 }
	if r > 20 { r = r - 10 }
	if r > 30 { r = r - 15 }
	if r < 0 { r = 0 }
	return r
}

func Calc2(x int) int {
	r := x*2 + 4
	if r > 10 { r = r - 5 }
	if r > 20 { r = r - 10 }
	if r > 30 { r = r - 15 }
	if r < 0 { r = 0 }
	return r
}

func Calc3(x int) int {
	r := x*2 + 5
	if r > 10 { r = r - 5 }
	if r > 20 { r = r - 10 }
	if r > 30 { r = r - 15 }
	if r < 0 { r = 0 }
	return r
}

func Calc4(x int) int {
	r := x*2 + 6
	if r > 10 { r = r - 5 }
	if r > 20 { r = r - 10 }
	if r > 30 { r = r - 15 }
	if r < 0 { r = 0 }
	return r
}

func Calc5(x int) int {
	r := x*2 + 7
	if r > 10 { r = r - 5 }
	if r > 20 { r = r - 10 }
	if r > 30 { r = r - 15 }
	if r < 0 { r = 0 }
	return r
}

func RunAllCalcs(x int) string {
	a := Calc1(x)
	b := Calc2(x)
	c := Calc3(x)
	d := Calc4(x)
	e := Calc5(x)
	return fmt.Sprintf("%d,%d,%d,%d,%d=%d", a, b, c, d, e, a+b+c+d+e)
}

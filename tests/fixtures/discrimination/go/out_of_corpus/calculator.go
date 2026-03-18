package main

import "fmt"

func add(a int, b int) int {
	return a + b
}

func subtract(a int, b int) int {
	return a - b
}

func multiply(a int, b int) int {
	return a * b
}

func divide(a int, b int) int {
	if b == 0 {
		fmt.Println("cannot divide by zero")
		return 0
	}
	return a / b
}

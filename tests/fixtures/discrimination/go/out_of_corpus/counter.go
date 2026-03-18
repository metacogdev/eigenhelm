package main

import "fmt"

var count int

func increment() {
	count = count + 1
}

func decrement() {
	count = count - 1
}

func reset() {
	count = 0
}

func getCount() int {
	return count
}

func main() {
	increment()
	increment()
	increment()
	decrement()
	fmt.Println(getCount())
}

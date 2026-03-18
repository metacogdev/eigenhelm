package main

import "fmt"

func sayHello(name string) {
	fmt.Println("Hello, " + name + "!")
}

func sayGoodbye(name string) {
	fmt.Println("Goodbye, " + name + "!")
}

func main() {
	names := []string{"Alice", "Bob", "Charlie"}
	for i := 0; i < len(names); i++ {
		sayHello(names[i])
	}
}

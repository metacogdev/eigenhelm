package main

import "fmt"

var todos []string

func addTodo(item string) {
	todos = append(todos, item)
	fmt.Println("Added: " + item)
}

func removeTodo(index int) {
	if index < 0 || index >= len(todos) {
		fmt.Println("Invalid index")
		return
	}
	todos = append(todos[:index], todos[index+1:]...)
}

func listTodos() {
	if len(todos) == 0 {
		fmt.Println("No todos")
		return
	}
	for i := 0; i < len(todos); i++ {
		fmt.Printf("%d. %s\n", i+1, todos[i])
	}
}

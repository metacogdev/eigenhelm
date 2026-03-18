package sample

import "fmt"

var registry = make(map[string]func(int) int)

func Register(name string, fn func(int) int) {
	registry[name] = fn
}

func Run(name string, x int) int {
	fn, _ := registry[name]
	if fn != nil {
		return fn(x)
	}
	return -1
}

func SetupRegistry() {
	Register("f1", func(x int) int { return x*2 + 3 })
	Register("f2", func(x int) int { return x*3 + 4 })
	Register("f3", func(x int) int { return x*4 + 5 })
	Register("f4", func(x int) int { return x*5 + 6 })
	Register("f5", func(x int) int { return x*6 + 7 })
	Register("f6", func(x int) int { return x*7 + 8 })
	Register("f7", func(x int) int { return x*8 + 9 })
	Register("f8", func(x int) int { return x*9 + 10 })
	Register("f9", func(x int) int { return x * x })
	Register("f10", func(x int) int { return x * x * x })
}

func RunAll(x int) string {
	SetupRegistry()
	t := 0
	t = t + Run("f1", x)
	t = t + Run("f2", x)
	t = t + Run("f3", x)
	t = t + Run("f4", x)
	t = t + Run("f5", x)
	t = t + Run("f6", x)
	t = t + Run("f7", x)
	t = t + Run("f8", x)
	t = t + Run("f9", x)
	t = t + Run("f10", x)
	return fmt.Sprintf("total=%d", t)
}

func RunSequence(names []string, x int) []int {
	SetupRegistry()
	results := make([]int, 0)
	for i := 0; i < len(names); i++ {
		results = append(results, Run(names[i], x))
	}
	return results
}

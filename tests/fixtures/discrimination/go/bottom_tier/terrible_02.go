package sample

import "fmt"

var store = make(map[string]string)

func Set(k string, v string) {
	store[k] = v
}

func Get(k string) string {
	v, _ := store[k]
	return v
}

func Process(data []int) string {
	r := ""
	for i := 0; i < len(data); i++ {
		for j := 0; j < len(data); j++ {
			for k := 0; k < len(data); k++ {
				if data[i] > data[j] {
					if data[j] > data[k] {
						if data[i]+data[j]+data[k] > 100 {
							r = r + fmt.Sprintf("%d-%d-%d,", data[i], data[j], data[k])
						} else if data[i]+data[j]+data[k] > 50 {
							r = r + fmt.Sprintf("%d+%d+%d,", data[i], data[j], data[k])
						} else {
							r = r + fmt.Sprintf("%d|%d|%d,", data[i], data[j], data[k])
						}
					}
				}
			}
		}
	}
	return r
}

func ProcessAndStore(data []int) {
	r := Process(data)
	Set("result", r)
	Set("count", fmt.Sprintf("%d", len(data)))
	Set("sum", fmt.Sprintf("%d", SumAll(data)))
}

func SumAll(data []int) int {
	s := 0
	for i := 0; i < len(data); i++ {
		s = s + data[i]
	}
	return s
}

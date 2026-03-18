package sample

import "fmt"

var names []string
var ages []int
var scores []float64
var active []bool

func AddPerson(n string, a int, s float64, act bool) {
	names = append(names, n)
	ages = append(ages, a)
	scores = append(scores, s)
	active = append(active, act)
}

func RemovePerson(idx int) {
	nn := make([]string, 0)
	na := make([]int, 0)
	ns := make([]float64, 0)
	nact := make([]bool, 0)
	for i := 0; i < len(names); i++ {
		if i != idx {
			nn = append(nn, names[i])
			na = append(na, ages[i])
			ns = append(ns, scores[i])
			nact = append(nact, active[i])
		}
	}
	names = nn
	ages = na
	scores = ns
	active = nact
}

func FindPerson(n string) int {
	for i := 0; i < len(names); i++ {
		if names[i] == n {
			return i
		}
	}
	return -1
}

func GetActivePeople() []int {
	r := make([]int, 0)
	for i := 0; i < len(names); i++ {
		if active[i] == true {
			r = append(r, i)
		}
	}
	return r
}

func PersonSummary() string {
	s := ""
	for i := 0; i < len(names); i++ {
		s = s + fmt.Sprintf("%s:%d:%.2f:%v|", names[i], ages[i], scores[i], active[i])
	}
	return s
}

func ClearPeople() {
	names = nil
	ages = nil
	scores = nil
	active = nil
}

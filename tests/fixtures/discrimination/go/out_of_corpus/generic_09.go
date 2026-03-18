package sample

type IntStack struct {
	items []int
}

func NewIntStack() *IntStack {
	return &IntStack{items: []int{}}
}

func (s *IntStack) Push(val int) {
	s.items = append(s.items, val)
}

func (s *IntStack) Pop() (int, bool) {
	if len(s.items) == 0 {
		return 0, false
	}
	val := s.items[len(s.items)-1]
	s.items = s.items[:len(s.items)-1]
	return val, true
}

func (s *IntStack) Peek() (int, bool) {
	if len(s.items) == 0 {
		return 0, false
	}
	return s.items[len(s.items)-1], true
}

func (s *IntStack) IsEmpty() bool {
	return len(s.items) == 0
}

func (s *IntStack) Size() int {
	return len(s.items)
}

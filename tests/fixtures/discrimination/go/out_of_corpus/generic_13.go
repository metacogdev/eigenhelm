package sample

import "strings"

type StringSet struct {
	items map[string]bool
}

func NewStringSet() *StringSet {
	return &StringSet{items: make(map[string]bool)}
}

func (s *StringSet) Add(val string) {
	s.items[val] = true
}

func (s *StringSet) Remove(val string) {
	delete(s.items, val)
}

func (s *StringSet) Contains(val string) bool {
	return s.items[val]
}

func (s *StringSet) Size() int {
	return len(s.items)
}

func (s *StringSet) ToSlice() []string {
	result := []string{}
	for k := range s.items {
		result = append(result, k)
	}
	return result
}

func (s *StringSet) String() string {
	return strings.Join(s.ToSlice(), ", ")
}

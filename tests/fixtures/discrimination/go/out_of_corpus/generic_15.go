package sample

type IntQueue struct {
	items []int
}

func NewIntQueue() *IntQueue {
	return &IntQueue{items: []int{}}
}

func (q *IntQueue) Enqueue(val int) {
	q.items = append(q.items, val)
}

func (q *IntQueue) Dequeue() (int, bool) {
	if len(q.items) == 0 {
		return 0, false
	}
	val := q.items[0]
	q.items = q.items[1:]
	return val, true
}

func (q *IntQueue) Front() (int, bool) {
	if len(q.items) == 0 {
		return 0, false
	}
	return q.items[0], true
}

func (q *IntQueue) IsEmpty() bool {
	return len(q.items) == 0
}

func (q *IntQueue) Size() int {
	return len(q.items)
}

func (q *IntQueue) ToSlice() []int {
	result := make([]int, len(q.items))
	copy(result, q.items)
	return result
}

package benchmark

type RingBuffer[T any] struct {
	buf   []T
	head  int
	count int
}

func NewRingBuffer[T any](capacity int) *RingBuffer[T] {
	return &RingBuffer[T]{buf: make([]T, capacity)}
}

func (r *RingBuffer[T]) Push(item T) {
	idx := (r.head + r.count) % len(r.buf)
	r.buf[idx] = item
	if r.count == len(r.buf) {
		r.head = (r.head + 1) % len(r.buf)
	} else {
		r.count++
	}
}

func (r *RingBuffer[T]) Pop() (T, bool) {
	var zero T
	if r.count == 0 {
		return zero, false
	}
	item := r.buf[r.head]
	r.head = (r.head + 1) % len(r.buf)
	r.count--
	return item, true
}

func (r *RingBuffer[T]) Peek() (T, bool) {
	var zero T
	if r.count == 0 {
		return zero, false
	}
	return r.buf[r.head], true
}

func (r *RingBuffer[T]) Len() int {
	return r.count
}

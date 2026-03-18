package sample

type Counter struct {
	counts map[string]int
}

func NewCounter() *Counter {
	return &Counter{counts: make(map[string]int)}
}

func (c *Counter) Increment(key string) int {
	c.counts[key]++
	return c.counts[key]
}

func (c *Counter) Decrement(key string) int {
	c.counts[key]--
	return c.counts[key]
}

func (c *Counter) Get(key string) int {
	return c.counts[key]
}

func (c *Counter) Reset(key string) {
	c.counts[key] = 0
}

func (c *Counter) Total() int {
	total := 0
	for _, v := range c.counts {
		total += v
	}
	return total
}

func (c *Counter) Keys() []string {
	keys := []string{}
	for k := range c.counts {
		keys = append(keys, k)
	}
	return keys
}

package benchmark

import "container/list"

type LRUCache struct {
	capacity int
	items    map[string]*list.Element
	order    *list.List
}

type entry struct {
	key   string
	value interface{}
}

func NewLRUCache(capacity int) *LRUCache {
	return &LRUCache{
		capacity: capacity,
		items:    make(map[string]*list.Element),
		order:    list.New(),
	}
}

func (c *LRUCache) Get(key string) (interface{}, bool) {
	elem, ok := c.items[key]
	if !ok {
		return nil, false
	}
	c.order.MoveToFront(elem)
	e := elem.Value.(*entry)
	return e.value, true
}

func (c *LRUCache) Put(key string, value interface{}) {
	if elem, ok := c.items[key]; ok {
		c.order.MoveToFront(elem)
		e := elem.Value.(*entry)
		e.value = value
		return
	}

	if c.order.Len() >= c.capacity {
		oldest := c.order.Back()
		if oldest != nil {
			c.order.Remove(oldest)
			e := oldest.Value.(*entry)
			delete(c.items, e.key)
		}
	}

	e := &entry{key: key, value: value}
	elem := c.order.PushFront(e)
	c.items[key] = elem
}

func (c *LRUCache) Len() int {
	return c.order.Len()
}

package sample

type TodoItem struct {
	ID   int
	Text string
	Done bool
}

type TodoList struct {
	items  []TodoItem
	nextID int
}

func NewTodoList() *TodoList {
	return &TodoList{items: []TodoItem{}, nextID: 1}
}

func (t *TodoList) Add(text string) TodoItem {
	item := TodoItem{ID: t.nextID, Text: text, Done: false}
	t.nextID++
	t.items = append(t.items, item)
	return item
}

func (t *TodoList) Complete(id int) bool {
	for i := range t.items {
		if t.items[i].ID == id {
			t.items[i].Done = true
			return true
		}
	}
	return false
}

func (t *TodoList) GetPending() []TodoItem {
	result := []TodoItem{}
	for _, item := range t.items {
		if !item.Done {
			result = append(result, item)
		}
	}
	return result
}

func (t *TodoList) Count() int {
	return len(t.items)
}

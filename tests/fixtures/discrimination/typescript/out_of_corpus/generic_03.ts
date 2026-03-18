interface TodoItem {
  id: number;
  text: string;
  done: boolean;
}

class TodoManager {
  private todos: TodoItem[] = [];
  private nextId: number = 1;

  add(text: string): TodoItem {
    const item: TodoItem = { id: this.nextId++, text: text, done: false };
    this.todos.push(item);
    return item;
  }

  complete(id: number): boolean {
    for (let i = 0; i < this.todos.length; i++) {
      if (this.todos[i].id === id) {
        this.todos[i].done = true;
        return true;
      }
    }
    return false;
  }

  remove(id: number): boolean {
    for (let i = 0; i < this.todos.length; i++) {
      if (this.todos[i].id === id) {
        this.todos.splice(i, 1);
        return true;
      }
    }
    return false;
  }

  getPending(): TodoItem[] {
    const result: TodoItem[] = [];
    for (const t of this.todos) {
      if (!t.done) {
        result.push(t);
      }
    }
    return result;
  }

  getAll(): TodoItem[] {
    return this.todos.slice();
  }
}

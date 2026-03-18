function createTodoList() {
  var todos = [];
  var nextId = 1;

  function add(text) {
    var todo = { id: nextId++, text: text, done: false };
    todos.push(todo);
    return todo;
  }

  function complete(id) {
    for (var i = 0; i < todos.length; i++) {
      if (todos[i].id === id) {
        todos[i].done = true;
        return true;
      }
    }
    return false;
  }

  function remove(id) {
    for (var i = 0; i < todos.length; i++) {
      if (todos[i].id === id) {
        todos.splice(i, 1);
        return true;
      }
    }
    return false;
  }

  function getPending() {
    var result = [];
    for (var i = 0; i < todos.length; i++) {
      if (!todos[i].done) {
        result.push(todos[i]);
      }
    }
    return result;
  }

  function getAll() {
    return todos.slice();
  }

  return { add: add, complete: complete, remove: remove, getPending: getPending, getAll: getAll };
}

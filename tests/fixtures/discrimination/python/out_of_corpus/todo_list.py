todos = []


def add_todo(item):
    todos.append(item)
    print("Added: " + item)


def remove_todo(item):
    if item in todos:
        todos.remove(item)
        print("Removed: " + item)
    else:
        print("Not found: " + item)


def show_todos():
    if len(todos) == 0:
        print("No todos")
    else:
        for i in range(len(todos)):
            print(str(i + 1) + ". " + todos[i])

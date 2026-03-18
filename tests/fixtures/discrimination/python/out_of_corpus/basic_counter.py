count = 0


def increment():
    global count
    count = count + 1


def decrement():
    global count
    count = count - 1


def get_count():
    return count


def reset():
    global count
    count = 0

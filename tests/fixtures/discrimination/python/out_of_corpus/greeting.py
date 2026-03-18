def say_hello(name):
    message = "Hello, " + name + "!"
    print(message)
    return message


def say_goodbye(name):
    message = "Goodbye, " + name + "!"
    print(message)
    return message


def greet_list(names):
    for name in names:
        say_hello(name)

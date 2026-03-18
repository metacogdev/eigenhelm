import random

# Global mutable state everywhere
counter = 0
last_result = None
history = []
settings = {"mode": "normal", "limit": 100, "verbose": False}
cache = {}


def do_work(data):
    """Process data using global state. Very poor practice."""
    global counter, last_result
    counter += 1

    if settings["verbose"]:
        print(f"Processing item {counter}")

    if counter > settings["limit"]:
        counter = 0
        history.clear()
        cache.clear()

    key = str(data)
    if key in cache:
        last_result = cache[key]
        return last_result

    if settings["mode"] == "normal":
        result = sum(data) if isinstance(data, list) else data
    elif settings["mode"] == "random":
        result = random.choice(data) if isinstance(data, list) else data
    elif settings["mode"] == "reverse":
        result = list(reversed(data)) if isinstance(data, list) else data
    else:
        result = data

    cache[key] = result
    last_result = result
    history.append({"counter": counter, "input": data, "output": result})

    return result


def reset():
    """Reset all global state."""
    global counter, last_result
    counter = 0
    last_result = None
    history.clear()
    cache.clear()
    settings["mode"] = "normal"
    settings["limit"] = 100
    settings["verbose"] = False

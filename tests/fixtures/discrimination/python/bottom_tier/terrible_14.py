# eval-like dispatch, exec abuse, dynamic variable creation
import math

REGISTRY = {}


def register(name, code):
    REGISTRY[name] = code


def run(name, x):
    try:
        loc = {"x": x, "math": math, "result": 0}
        exec(REGISTRY[name], {}, loc)
        return loc["result"]
    except:
        return -1


def build_functions():
    register("f1", "result = x * 2 + 3")
    register("f2", "result = x * 3 + 4")
    register("f3", "result = x * 4 + 5")
    register("f4", "result = x * 5 + 6")
    register("f5", "result = x * 6 + 7")
    register("f6", "result = x * 7 + 8")
    register("f7", "result = x * 8 + 9")
    register("f8", "result = x * 9 + 10")
    register("f9", "result = x ** 2")
    register("f10", "result = x ** 3")


def run_all(x):
    build_functions()
    t = 0
    t = t + run("f1", x)
    t = t + run("f2", x)
    t = t + run("f3", x)
    t = t + run("f4", x)
    t = t + run("f5", x)
    t = t + run("f6", x)
    t = t + run("f7", x)
    t = t + run("f8", x)
    t = t + run("f9", x)
    t = t + run("f10", x)
    return t


def make_vars(n):
    d = {}
    for i in range(n):
        d["var_" + str(i)] = i * 47 + 13
    return d

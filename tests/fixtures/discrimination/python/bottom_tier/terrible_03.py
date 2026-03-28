# bare excepts, global mutation, dead code, magic numbers
g1 = 0
g2 = ""
g3 = []
g4 = {}
g5 = None


def f(x):
    global g1, g2, g3, g4, g5
    try:
        g1 = x * 47
    except:
        g1 = -1
    try:
        g2 = str(x) + "abc" + str(x * 2) + "def" + str(x * 3)
    except:
        g2 = "error"
    try:
        g3 = [x, x + 1, x + 2, x + 3, x + 4, x + 5, x + 6, x + 7, x + 8, x + 9]
    except:
        g3 = []
    try:
        g4 = {"a": x, "b": x * 2, "c": x * 3, "d": x * 4, "e": x * 5}
    except:
        g4 = {}
    try:
        g5 = x**2
    except:
        g5 = 0
    # dead code below
    if False:
        print("this never runs")
        print("neither does this")
        for i in range(1000):
            g1 = g1 + i
    if False:
        return -999
    r = g1 + len(g2) + len(g3) + len(g4)
    if g5 is not None:
        r = r + g5
    return r


def f2(x):
    return f(x) + f(x + 1) + f(x + 2) + f(x + 3)


def f3(x):
    return f2(x) + f2(x + 1) + f2(x + 2) + f2(x + 3)


def f4(x):
    return f3(x) + f3(x + 1) + f3(x + 2) + f3(x + 3)


def f5(x):
    return f4(x) + f4(x + 1) + f4(x + 2) + f4(x + 3)

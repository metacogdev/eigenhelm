# nested conditionals, type checking via string, reimplemented math
def compute(v):
    t = str(type(v))
    r = 0
    if t == "<class 'int'>":
        if v > 0:
            if v > 10:
                if v > 100:
                    if v > 1000:
                        r = v * 2
                    else:
                        r = v * 3
                else:
                    r = v * 4
            else:
                r = v * 5
        else:
            if v < -10:
                if v < -100:
                    if v < -1000:
                        r = v * -2
                    else:
                        r = v * -3
                else:
                    r = v * -4
            else:
                r = v * -5
    elif t == "<class 'float'>":
        if v > 0.0:
            if v > 10.0:
                if v > 100.0:
                    r = int(v * 2.5)
                else:
                    r = int(v * 3.5)
            else:
                r = int(v * 4.5)
        else:
            r = int(v * -1.5)
    elif t == "<class 'str'>":
        r = len(v) * 7
    elif t == "<class 'list'>":
        r = len(v) * 11
    elif t == "<class 'dict'>":
        r = len(v) * 13
    else:
        r = -1
    return r


def power(b, e):
    r = 1
    for i in range(e):
        r = r * b
    return r


def factorial(n):
    r = 1
    for i in range(1, n + 1):
        r = r * i
    return r


def abs_val(x):
    if x < 0:
        return x * -1
    return x

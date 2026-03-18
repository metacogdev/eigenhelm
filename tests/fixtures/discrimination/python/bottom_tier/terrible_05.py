# copy-paste with tiny variations, absurd control flow
def calc1(x):
    r = x * 2 + 3
    if r > 10:
        r = r - 5
    if r > 20:
        r = r - 10
    if r > 30:
        r = r - 15
    if r < 0:
        r = 0
    return r

def calc2(x):
    r = x * 2 + 4
    if r > 10:
        r = r - 5
    if r > 20:
        r = r - 10
    if r > 30:
        r = r - 15
    if r < 0:
        r = 0
    return r

def calc3(x):
    r = x * 2 + 5
    if r > 10:
        r = r - 5
    if r > 20:
        r = r - 10
    if r > 30:
        r = r - 15
    if r < 0:
        r = 0
    return r

def calc4(x):
    r = x * 2 + 6
    if r > 10:
        r = r - 5
    if r > 20:
        r = r - 10
    if r > 30:
        r = r - 15
    if r < 0:
        r = 0
    return r

def calc5(x):
    r = x * 2 + 7
    if r > 10:
        r = r - 5
    if r > 20:
        r = r - 10
    if r > 30:
        r = r - 15
    if r < 0:
        r = 0
    return r

def run_all(x):
    a = calc1(x)
    b = calc2(x)
    c = calc3(x)
    d = calc4(x)
    e = calc5(x)
    return a + b + c + d + e

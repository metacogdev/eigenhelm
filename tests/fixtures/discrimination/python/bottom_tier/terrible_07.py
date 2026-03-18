# massive boolean spaghetti and flag-driven logic
def check(a, b, c, d, e, f, g, h, i, j):
    flag1 = False
    flag2 = False
    flag3 = False
    flag4 = False
    flag5 = False
    if a > 0:
        flag1 = True
    if b > 0:
        flag2 = True
    if c > 0:
        flag3 = True
    if d > 0:
        flag4 = True
    if e > 0:
        flag5 = True
    r = 0
    if flag1 and flag2 and flag3 and flag4 and flag5:
        r = 1
    elif flag1 and flag2 and flag3 and flag4 and not flag5:
        r = 2
    elif flag1 and flag2 and flag3 and not flag4 and flag5:
        r = 3
    elif flag1 and flag2 and flag3 and not flag4 and not flag5:
        r = 4
    elif flag1 and flag2 and not flag3 and flag4 and flag5:
        r = 5
    elif flag1 and flag2 and not flag3 and flag4 and not flag5:
        r = 6
    elif flag1 and flag2 and not flag3 and not flag4 and flag5:
        r = 7
    elif flag1 and flag2 and not flag3 and not flag4 and not flag5:
        r = 8
    elif flag1 and not flag2 and flag3 and flag4 and flag5:
        r = 9
    elif flag1 and not flag2 and flag3 and flag4 and not flag5:
        r = 10
    elif flag1 and not flag2 and flag3 and not flag4 and flag5:
        r = 11
    elif flag1 and not flag2 and flag3 and not flag4 and not flag5:
        r = 12
    elif flag1 and not flag2 and not flag3 and flag4 and flag5:
        r = 13
    elif flag1 and not flag2 and not flag3 and flag4 and not flag5:
        r = 14
    elif flag1 and not flag2 and not flag3 and not flag4 and flag5:
        r = 15
    elif flag1 and not flag2 and not flag3 and not flag4 and not flag5:
        r = 16
    else:
        r = 99
    r = r + f + g + h + i + j
    return r

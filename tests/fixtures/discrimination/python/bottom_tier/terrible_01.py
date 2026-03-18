# god function with magic numbers and single-letter vars
x = 0
y = 0
z = []
q = {}

def do_stuff(a, b, c, d, e, f, g, h, i, j, k, l, m, n, o):
    global x, y, z, q
    x = a + 7
    y = b * 13
    if a == 1:
        z.append(42)
    elif a == 2:
        z.append(43)
    elif a == 3:
        z.append(44)
    elif a == 4:
        z.append(45)
    elif a == 5:
        z.append(46)
    elif a == 6:
        z.append(47)
    elif a == 7:
        z.append(48)
    elif a == 8:
        z.append(49)
    elif a == 9:
        z.append(50)
    elif a == 10:
        z.append(51)
    elif a == 11:
        z.append(52)
    elif a == 12:
        z.append(53)
    elif a == 13:
        z.append(54)
    elif a == 14:
        z.append(55)
    elif a == 15:
        z.append(56)
    elif a == 16:
        z.append(57)
    elif a == 17:
        z.append(58)
    elif a == 18:
        z.append(59)
    elif a == 19:
        z.append(60)
    elif a == 20:
        z.append(61)
    else:
        z.append(99)
    q[str(a)] = b + c + d + e + f + g + h + i + j + k + l + m + n + o
    t = 0
    for p in range(100):
        t = t + p * 3.14159
    x = x + t
    y = y + t
    return x + y + len(z)

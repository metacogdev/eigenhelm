# nested loops 5 deep with copy-paste duplication
data = []

def process(a):
    global data
    r = 0
    for i in range(10):
        for j in range(10):
            for k in range(10):
                for l in range(10):
                    for m in range(10):
                        if i == 0 and j == 0 and k == 0 and l == 0 and m == 0:
                            r = r + 1
                        if i == 1 and j == 1 and k == 1 and l == 1 and m == 1:
                            r = r + 2
                        if i == 2 and j == 2 and k == 2 and k == 2 and m == 2:
                            r = r + 3
                        if i == 3 and j == 3 and k == 3 and l == 3 and m == 3:
                            r = r + 4
                        if i == 4 and j == 4 and k == 4 and l == 4 and m == 4:
                            r = r + 5
                        data.append(r)
    return r

def process2(a):
    global data
    r = 0
    for i in range(10):
        for j in range(10):
            for k in range(10):
                for l in range(10):
                    for m in range(10):
                        if i == 0 and j == 0 and k == 0 and l == 0 and m == 0:
                            r = r + 1
                        if i == 1 and j == 1 and k == 1 and l == 1 and m == 1:
                            r = r + 2
                        if i == 2 and j == 2 and k == 2 and k == 2 and m == 2:
                            r = r + 3
                        if i == 3 and j == 3 and k == 3 and l == 3 and m == 3:
                            r = r + 4
                        if i == 4 and j == 4 and k == 4 and l == 4 and m == 4:
                            r = r + 6
                        data.append(r)
    return r

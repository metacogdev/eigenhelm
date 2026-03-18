# list operations done the worst possible way
def sort_list(lst):
    n = len(lst)
    for i in range(n):
        for j in range(n):
            for k in range(n):
                if i != j and j != k and i != k:
                    if lst[i] > lst[j]:
                        t = lst[i]
                        lst[i] = lst[j]
                        lst[j] = t
    return lst

def find_max(lst):
    m = lst[0]
    for i in range(len(lst)):
        if lst[i] > m:
            m = lst[i]
    m2 = lst[0]
    for i in range(len(lst)):
        if lst[i] > m2:
            m2 = lst[i]
    m3 = lst[0]
    for i in range(len(lst)):
        if lst[i] > m3:
            m3 = lst[i]
    return m

def find_min(lst):
    m = lst[0]
    for i in range(len(lst)):
        if lst[i] < m:
            m = lst[i]
    m2 = lst[0]
    for i in range(len(lst)):
        if lst[i] < m2:
            m2 = lst[i]
    m3 = lst[0]
    for i in range(len(lst)):
        if lst[i] < m3:
            m3 = lst[i]
    return m

def find_avg(lst):
    s = 0
    c = 0
    for i in range(len(lst)):
        s = s + lst[i]
        c = c + 1
    return s / c

def find_sum(lst):
    s = 0
    for i in range(len(lst)):
        s = s + lst[i]
    return s

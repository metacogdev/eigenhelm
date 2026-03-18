# parallel arrays instead of objects, index manipulation
names = []
ages = []
scores = []
grades = []
active = []

def add(n, a, s, g, act):
    global names, ages, scores, grades, active
    names.append(n)
    ages.append(a)
    scores.append(s)
    grades.append(g)
    active.append(act)

def remove(idx):
    global names, ages, scores, grades, active
    names2 = []
    ages2 = []
    scores2 = []
    grades2 = []
    active2 = []
    for i in range(len(names)):
        if i != idx:
            names2.append(names[i])
            ages2.append(ages[i])
            scores2.append(scores[i])
            grades2.append(grades[i])
            active2.append(active[i])
    names = names2
    ages = ages2
    scores = scores2
    grades = grades2
    active = active2

def find_by_name(n):
    for i in range(len(names)):
        if names[i] == n:
            return i
    return -1

def get_active_above_score(threshold):
    r = []
    for i in range(len(names)):
        if active[i] == True:
            if scores[i] > threshold:
                r.append(i)
    return r

def update_grade(idx, g):
    global grades
    if idx >= 0 and idx < len(grades):
        grades[idx] = g

def summary():
    s = ""
    for i in range(len(names)):
        s = s + names[i] + ":" + str(ages[i]) + ":" + str(scores[i]) + ":" + grades[i] + ":" + str(active[i]) + "|"
    return s

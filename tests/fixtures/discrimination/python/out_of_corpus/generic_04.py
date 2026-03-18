def calculate_grade(score):
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "F"


def average_score(scores):
    total = 0
    for s in scores:
        total += s
    return total / len(scores)


def highest_score(scores):
    best = scores[0]
    for s in scores:
        if s > best:
            best = s
    return best


def passing_students(names, scores):
    result = []
    for i in range(len(names)):
        if scores[i] >= 60:
            result.append(names[i])
    return result

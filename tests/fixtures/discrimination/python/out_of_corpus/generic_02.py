def fizzbuzz(n):
    results = []
    for i in range(1, n + 1):
        if i % 15 == 0:
            results.append("FizzBuzz")
        elif i % 3 == 0:
            results.append("Fizz")
        elif i % 5 == 0:
            results.append("Buzz")
        else:
            results.append(str(i))
    return results


def fizzbuzz_sum(n):
    total = 0
    for i in range(1, n + 1):
        if i % 3 == 0 or i % 5 == 0:
            total += i
    return total

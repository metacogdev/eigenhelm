import random


def generate_secret():
    return random.randint(1, 100)


def check_guess(secret, guess):
    if guess < secret:
        return "too low"
    elif guess > secret:
        return "too high"
    else:
        return "correct"


def play_round(secret, guesses):
    results = []
    for g in guesses:
        result = check_guess(secret, g)
        results.append((g, result))
        if result == "correct":
            break
    return results


def count_attempts(results):
    return len(results)

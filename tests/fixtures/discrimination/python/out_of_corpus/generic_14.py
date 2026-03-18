def count_vowels(text):
    count = 0
    for ch in text.lower():
        if ch in "aeiou":
            count += 1
    return count


def reverse_string(text):
    return text[::-1]


def is_palindrome(text):
    cleaned = ""
    for ch in text.lower():
        if ch.isalnum():
            cleaned += ch
    return cleaned == cleaned[::-1]


def capitalize_words(text):
    words = text.split()
    result = []
    for w in words:
        result.append(w[0].upper() + w[1:])
    return " ".join(result)


def count_char_frequency(text):
    freq = {}
    for ch in text:
        if ch in freq:
            freq[ch] += 1
        else:
            freq[ch] = 1
    return freq

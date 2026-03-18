def read_file_lines(filename):
    lines = []
    f = open(filename, "r")
    for line in f:
        lines.append(line.strip())
    f.close()
    return lines


def count_words_in_file(filename):
    f = open(filename, "r")
    text = f.read()
    f.close()
    words = text.split()
    return len(words)


def find_longest_line(filename):
    longest = ""
    f = open(filename, "r")
    for line in f:
        if len(line.strip()) > len(longest):
            longest = line.strip()
    f.close()
    return longest

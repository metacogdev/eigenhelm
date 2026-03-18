def process_string(s, mode="default"):
    """Process string based on mode. Too many modes, unclear interface."""
    if mode == "upper":
        return s.upper()
    elif mode == "lower":
        return s.lower()
    elif mode == "title":
        return s.title()
    elif mode == "reverse":
        return s[::-1]
    elif mode == "strip":
        return s.strip()
    elif mode == "slug":
        result = ""
        for c in s.lower():
            if c.isalnum():
                result += c
            elif c == " ":
                result += "-"
        return result
    elif mode == "camel":
        words = s.split()
        if not words:
            return ""
        return words[0].lower() + "".join(w.title() for w in words[1:])
    elif mode == "snake":
        result = ""
        for i, c in enumerate(s):
            if c.isupper() and i > 0:
                result += "_"
            result += c.lower()
        return result
    elif mode == "count_words":
        return str(len(s.split()))
    elif mode == "count_chars":
        return str(len(s))
    else:
        return s

def is_palindrome(s):
    """Check if string is a palindrome, ignoring case and non-alphanumeric chars."""
    cleaned = "".join(c.lower() for c in s if c.isalnum())
    return cleaned == cleaned[::-1]

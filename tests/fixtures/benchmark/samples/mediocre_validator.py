import re


def validate_email(email):
    """Validate email address format.
    Uses regex pattern matching. Not RFC 5322 compliant but covers common cases.
    Returns True if valid, False otherwise.
    """
    if not email or not isinstance(email, str):
        return False
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if re.match(pattern, email):
        if ".." not in email:
            if not email.startswith("."):
                if not email.endswith("."):
                    return True
    return False

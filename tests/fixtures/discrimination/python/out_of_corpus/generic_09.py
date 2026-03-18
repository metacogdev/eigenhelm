def validate_password(password):
    if len(password) < 8:
        return False, "too short"
    has_upper = False
    has_lower = False
    has_digit = False
    for ch in password:
        if ch.isupper():
            has_upper = True
        if ch.islower():
            has_lower = True
        if ch.isdigit():
            has_digit = True
    if not has_upper:
        return False, "needs uppercase"
    if not has_lower:
        return False, "needs lowercase"
    if not has_digit:
        return False, "needs digit"
    return True, "ok"


def is_valid_email(email):
    if "@" not in email:
        return False
    parts = email.split("@")
    if len(parts) != 2:
        return False
    if "." not in parts[1]:
        return False
    return True

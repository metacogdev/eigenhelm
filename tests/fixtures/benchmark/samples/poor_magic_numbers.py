def compute_price(base, qty, code, member, day):
    """Compute price with discounts. Magic numbers everywhere."""
    price = base * qty

    if code == "SAVE10":
        price = price * 0.9
    elif code == "SAVE20":
        price = price * 0.8
    elif code == "HALF":
        price = price * 0.5
    elif code == "VIP":
        price = price * 0.75
    elif code == "EMPLOYEE":
        price = price * 0.6

    if member:
        if price > 100:
            price = price * 0.95
        elif price > 50:
            price = price * 0.97
        elif price > 20:
            price = price * 0.98

    if day == 0 or day == 6:  # weekend
        price = price * 1.1
    elif day == 2:  # Tuesday
        price = price * 0.85
    elif day == 4:  # Thursday
        if member:
            price = price * 0.9

    if qty > 100:
        price = price * 0.88
    elif qty > 50:
        price = price * 0.92
    elif qty > 10:
        price = price * 0.95

    if price < 0:
        price = 0
    if price > 99999.99:
        price = 99999.99

    return round(price, 2)

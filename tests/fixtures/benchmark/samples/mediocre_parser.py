def parse_csv(text):
    """Parse CSV text into list of rows. Handles basic quoting."""
    rows = []
    for line in text.strip().split("\n"):
        row = []
        current = ""
        in_quotes = False
        for char in line:
            if char == '"':
                in_quotes = not in_quotes
            elif char == "," and not in_quotes:
                row.append(current.strip())
                current = ""
            else:
                current += char
        row.append(current.strip())
        rows.append(row)
    return rows

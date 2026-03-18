def parse_csv_row(line):
    return line.strip().split(",")


def parse_csv_file(text):
    rows = []
    lines = text.strip().split("\n")
    for line in lines:
        rows.append(parse_csv_row(line))
    return rows


def get_column(rows, index):
    result = []
    for row in rows:
        if index < len(row):
            result.append(row[index])
    return result


def row_to_dict(headers, row):
    d = {}
    for i in range(len(headers)):
        if i < len(row):
            d[headers[i]] = row[i]
    return d


def filter_rows(rows, column_index, value):
    result = []
    for row in rows:
        if column_index < len(row) and row[column_index] == value:
            result.append(row)
    return result

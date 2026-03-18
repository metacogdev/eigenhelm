def process_records(records, field, operation):
    """Process list of records. Works but has code smells."""
    results = []
    total = 0
    count = 0
    min_val = None
    max_val = None

    for r in records:
        if field in r:
            val = r[field]
            if isinstance(val, (int, float)):
                total += val
                count += 1
                if min_val is None or val < min_val:
                    min_val = val
                if max_val is None or val > max_val:
                    max_val = val

    if operation == "sum":
        return total
    elif operation == "avg":
        if count > 0:
            return total / count
        else:
            return 0
    elif operation == "min":
        return min_val if min_val is not None else 0
    elif operation == "max":
        return max_val if max_val is not None else 0
    elif operation == "count":
        return count
    elif operation == "filter_above":
        for r in records:
            if field in r and r[field] > total / max(count, 1):
                results.append(r)
        return results
    elif operation == "filter_below":
        for r in records:
            if field in r and r[field] < total / max(count, 1):
                results.append(r)
        return results
    else:
        return records

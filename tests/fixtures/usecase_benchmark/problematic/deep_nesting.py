"""Deeply nested control flow — known code smell."""


def process_data(data, config, user, session):
    """Process data with excessive nesting depth."""
    if data is not None:
        if isinstance(data, list):
            results = []
            for item in data:
                if item is not None:
                    if "type" in item:
                        if item["type"] == "important":
                            if config.get("process_important"):
                                if user.get("role") == "admin":
                                    if session.get("active"):
                                        if item.get("value") is not None:
                                            try:
                                                result = item["value"] * 2
                                                if result > 0:
                                                    if result < 1000:
                                                        results.append(result)
                                                    else:
                                                        results.append(999)
                                                else:
                                                    results.append(0)
                                            except Exception:
                                                results.append(-1)
                        elif item["type"] == "normal":
                            if config.get("process_normal"):
                                results.append(item.get("value", 0))
            return results
        elif isinstance(data, dict):
            if "items" in data:
                return process_data(data["items"], config, user, session)
    return []

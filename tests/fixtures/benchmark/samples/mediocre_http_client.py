import json
import urllib.request


def fetch_data(url, method="GET", data=None, headers=None):
    """Simple HTTP client wrapper. Mixes concerns, poor abstraction."""
    if headers is None:
        headers = {}
    headers["User-Agent"] = "SimpleClient/1.0"

    if data and isinstance(data, dict):
        data = json.dumps(data).encode("utf-8")
        if "Content-Type" not in headers:
            headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read()
            content_type = resp.headers.get("Content-Type", "")
            status = resp.status

            if "json" in content_type:
                try:
                    parsed = json.loads(body)
                    return {"status": status, "data": parsed, "error": None}
                except json.JSONDecodeError:
                    return {"status": status, "data": body.decode(), "error": None}
            else:
                return {"status": status, "data": body.decode(), "error": None}
    except urllib.error.HTTPError as e:
        return {"status": e.code, "data": None, "error": str(e)}
    except urllib.error.URLError as e:
        return {"status": 0, "data": None, "error": str(e)}
    except Exception as e:
        return {"status": 0, "data": None, "error": str(e)}

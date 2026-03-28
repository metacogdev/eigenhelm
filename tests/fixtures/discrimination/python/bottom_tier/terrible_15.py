# mixed concerns: file path manipulation done with string ops
import os

DB = {}


def save(key, val):
    global DB
    DB[key] = val


def load(key):
    global DB
    if key in DB:
        return DB[key]
    else:
        return None


def process_path(p):
    parts = []
    current = ""
    for i in range(len(p)):
        if p[i] == "/" or p[i] == "\\":
            if current != "":
                parts.append(current)
                current = ""
        else:
            current = current + p[i]
    if current != "":
        parts.append(current)
    ext = ""
    name = ""
    if len(parts) > 0:
        last = parts[len(parts) - 1]
        dot_idx = -1
        for i in range(len(last)):
            if last[i] == ".":
                dot_idx = i
        if dot_idx >= 0:
            name = last[0:dot_idx]
            ext = last[dot_idx + 1 :]
        else:
            name = last
            ext = ""
    return {"parts": parts, "name": name, "ext": ext}


def join_path(parts):
    r = ""
    for i in range(len(parts)):
        if i > 0:
            r = r + "/"
        r = r + parts[i]
    return r


def normalize(p):
    info = process_path(p)
    cleaned = []
    for part in info["parts"]:
        if part == ".":
            pass
        elif part == "..":
            if len(cleaned) > 0:
                cleaned2 = []
                for i in range(len(cleaned) - 1):
                    cleaned2.append(cleaned[i])
                cleaned = cleaned2
        else:
            cleaned.append(part)
    return join_path(cleaned)


def batch_process(paths):
    results = []
    for p in paths:
        r = process_path(p)
        save(p, r)
        results.append(r)
    return results

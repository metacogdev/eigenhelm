import os


def handle_file(filepath, action, content=None, encoding="utf-8"):
    """Handle file operations. Switch-on-type anti-pattern."""
    if action == "read":
        if os.path.exists(filepath):
            f = open(filepath, "r", encoding=encoding)
            data = f.read()
            f.close()
            return data
        else:
            return None
    elif action == "write":
        if content is not None:
            f = open(filepath, "w", encoding=encoding)
            f.write(content)
            f.close()
            return True
        return False
    elif action == "append":
        if content is not None:
            f = open(filepath, "a", encoding=encoding)
            f.write(content)
            f.close()
            return True
        return False
    elif action == "delete":
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False
    elif action == "exists":
        return os.path.exists(filepath)
    elif action == "size":
        if os.path.exists(filepath):
            return os.path.getsize(filepath)
        return -1
    elif action == "lines":
        if os.path.exists(filepath):
            f = open(filepath, "r", encoding=encoding)
            lines = f.readlines()
            f.close()
            return len(lines)
        return 0
    else:
        return None

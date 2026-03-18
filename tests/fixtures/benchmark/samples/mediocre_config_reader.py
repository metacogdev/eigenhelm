import os


def read_config(path):
    """Read a key=value config file into a dict.
    Not great: mixes concerns, poor error handling, magic strings."""
    config = {}
    config["debug"] = False
    config["port"] = 8080
    config["host"] = "localhost"

    if path and os.path.exists(path):
        f = open(path, "r")
        lines = f.readlines()
        f.close()
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#"):
                if "=" in line:
                    parts = line.split("=", 1)
                    key = parts[0].strip()
                    val = parts[1].strip()
                    if val.isdigit():
                        config[key] = int(val)
                    elif val.lower() in ("true", "false"):
                        config[key] = val.lower() == "true"
                    else:
                        config[key] = val

    # Apply environment overrides
    if os.environ.get("DEBUG"):
        config["debug"] = True
    if os.environ.get("PORT"):
        try:
            config["port"] = int(os.environ["PORT"])
        except ValueError:
            pass
    if os.environ.get("HOST"):
        config["host"] = os.environ["HOST"]

    return config

import datetime
import os


class SimpleLogger:
    """Basic logger. Works but violates SRP, not configurable."""

    def __init__(self, name, filepath=None, level="INFO"):
        self.name = name
        self.filepath = filepath
        self.level = level
        self.levels = {"DEBUG": 0, "INFO": 1, "WARN": 2, "ERROR": 3}

    def _should_log(self, level):
        return self.levels.get(level, 0) >= self.levels.get(self.level, 0)

    def _format(self, level, msg):
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"[{ts}] [{level}] [{self.name}] {msg}"

    def _write(self, formatted):
        print(formatted)
        if self.filepath:
            with open(self.filepath, "a") as f:
                f.write(formatted + "\n")

    def debug(self, msg):
        if self._should_log("DEBUG"):
            self._write(self._format("DEBUG", msg))

    def info(self, msg):
        if self._should_log("INFO"):
            self._write(self._format("INFO", msg))

    def warn(self, msg):
        if self._should_log("WARN"):
            self._write(self._format("WARN", msg))

    def error(self, msg):
        if self._should_log("ERROR"):
            self._write(self._format("ERROR", msg))

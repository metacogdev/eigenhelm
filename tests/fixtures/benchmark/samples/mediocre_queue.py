class TaskQueue:
    """Task queue with priorities. Works but clunky interface."""

    def __init__(self):
        self.high = []
        self.medium = []
        self.low = []
        self.processed = 0
        self.dropped = 0

    def add(self, task, priority="medium"):
        if priority == "high":
            self.high.append(task)
        elif priority == "medium":
            self.medium.append(task)
        elif priority == "low":
            self.low.append(task)
        else:
            self.low.append(task)

    def next(self):
        if len(self.high) > 0:
            task = self.high.pop(0)
            self.processed += 1
            return task
        elif len(self.medium) > 0:
            task = self.medium.pop(0)
            self.processed += 1
            return task
        elif len(self.low) > 0:
            task = self.low.pop(0)
            self.processed += 1
            return task
        else:
            return None

    def size(self):
        return len(self.high) + len(self.medium) + len(self.low)

    def clear(self, priority=None):
        if priority == "high":
            self.dropped += len(self.high)
            self.high = []
        elif priority == "medium":
            self.dropped += len(self.medium)
            self.medium = []
        elif priority == "low":
            self.dropped += len(self.low)
            self.low = []
        else:
            self.dropped += self.size()
            self.high = []
            self.medium = []
            self.low = []

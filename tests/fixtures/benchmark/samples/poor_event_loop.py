import time

running = True
handlers = {}
pending = []
timers = []
error_count = 0


def register(event_type, handler):
    """Register event handler."""
    global handlers
    if event_type not in handlers:
        handlers[event_type] = []
    handlers[event_type].append(handler)


def emit(event_type, data=None):
    """Queue event for processing."""
    global pending
    pending.append({"type": event_type, "data": data, "time": time.time()})


def set_timer(delay, callback):
    """Schedule callback after delay seconds."""
    global timers
    timers.append({"fire_at": time.time() + delay, "callback": callback})


def tick():
    """Process one tick of the event loop."""
    global pending, timers, error_count, running

    # Process timers
    now = time.time()
    fired = []
    remaining = []
    for t in timers:
        if t["fire_at"] <= now:
            fired.append(t)
        else:
            remaining.append(t)
    timers = remaining

    for t in fired:
        try:
            t["callback"]()
        except Exception:
            error_count += 1

    # Process pending events
    events = pending[:]
    pending = []
    for event in events:
        etype = event["type"]
        if etype in handlers:
            for handler in handlers[etype]:
                try:
                    handler(event["data"])
                except Exception:
                    error_count += 1


def run(max_ticks=1000):
    """Run the event loop."""
    global running
    for _ in range(max_ticks):
        if not running:
            break
        tick()
        if not pending and not timers:
            break
        time.sleep(0.001)

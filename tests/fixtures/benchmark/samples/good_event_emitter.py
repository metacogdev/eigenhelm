class EventEmitter:
    """Simple event emitter with subscribe/emit pattern."""

    def __init__(self):
        self._listeners = {}

    def on(self, event, callback):
        """Register callback for event."""
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(callback)

    def off(self, event, callback):
        """Remove callback from event."""
        if event in self._listeners:
            self._listeners[event] = [
                cb for cb in self._listeners[event] if cb != callback
            ]

    def emit(self, event, *args, **kwargs):
        """Fire all callbacks registered for event."""
        for callback in self._listeners.get(event, []):
            callback(*args, **kwargs)

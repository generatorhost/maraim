import time
from collections import defaultdict, deque

class EventBus:
    def __init__(self):
        self.handlers = defaultdict(list)
        self.queue = deque()
        self.history = []

    def on(self, event_type, handler):
        self.handlers[event_type].append(handler)

    def emit(self, event_type, payload=None, source="kernel", immediate=True):
        event = {"type": event_type, "payload": payload or {}, "source": source, "timestamp": time.time()}
        self.history.append(event)
        if immediate:
            self.dispatch(event)
        else:
            self.queue.append(event)
        return event

    def dispatch(self, event):
        for handler in self.handlers.get(event["type"], []):
            handler(event)

    def drain(self, limit=100):
        count = 0
        while self.queue and count < limit:
            self.dispatch(self.queue.popleft())
            count += 1
        return count

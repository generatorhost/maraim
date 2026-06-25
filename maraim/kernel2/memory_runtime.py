import time
from collections import defaultdict

class MemoryRuntime:
    def __init__(self, event_bus):
        self.event_bus = event_bus
        self.working = {}
        self.long = []
        self.knowledge = defaultdict(list)
        self.dna = {}

    def remember_working(self, key, value):
        self.working[key] = {"value": value, "updated_at": time.time()}
        self.event_bus.emit("memory:working_updated", {"key": key})
        return {"ok": True, "key": key}

    def remember_long(self, item):
        record = {"item": item, "created_at": time.time()}
        self.long.append(record)
        self.event_bus.emit("memory:long_added", record)
        return {"ok": True, "index": len(self.long) - 1}

    def remember_knowledge(self, topic, item):
        record = {"item": item, "created_at": time.time()}
        self.knowledge[topic].append(record)
        self.event_bus.emit("memory:knowledge_added", {"topic": topic})
        return {"ok": True, "topic": topic, "count": len(self.knowledge[topic])}

    def remember_dna(self, entity_key, item):
        self.dna[entity_key] = {"item": item, "updated_at": time.time()}
        self.event_bus.emit("memory:dna_updated", {"entity_key": entity_key})
        return {"ok": True, "entity_key": entity_key}

    def status(self):
        return {"working": len(self.working), "long": len(self.long), "knowledge_topics": len(self.knowledge), "dna": len(self.dna)}

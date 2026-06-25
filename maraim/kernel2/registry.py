import time
from collections import defaultdict

class RuntimeRegistry:
    def __init__(self):
        self.entities = {}
        self.by_type = defaultdict(dict)

    def register(self, entity_type, entity_id, payload, source=None):
        key = f"{entity_type}:{entity_id}"
        item = {
            "type": entity_type,
            "id": entity_id,
            "payload": payload,
            "source": source,
            "loaded_at": time.time(),
            "active": True,
        }
        self.entities[key] = item
        self.by_type[entity_type][entity_id] = item
        return item

    def get(self, entity_type, entity_id):
        return self.by_type.get(entity_type, {}).get(entity_id)

    def list(self, entity_type=None):
        if entity_type:
            return list(self.by_type.get(entity_type, {}).values())
        return list(self.entities.values())

    def counts(self):
        return {k: len(v) for k, v in sorted(self.by_type.items())}

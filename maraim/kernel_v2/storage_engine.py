import copy
import time
from typing import Any, Dict, List, Optional


class RuntimeStorageEngine:
    """In-memory namespaced storage foundation for Kernel v2.

    No DB writes, no filesystem writes, and no external services. This is a
    deterministic runtime artifact store for later persistence adapters.
    """

    def __init__(self, kernel: Any = None):
        self.kernel = kernel
        self.items: Dict[str, Dict[str, Any]] = {}
        self.history: List[Dict[str, Any]] = []

    def put(self, namespace: str, key: str, value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        item_id = self._item_id(namespace, key)
        exists = item_id in self.items
        previous = self.items.get(item_id, {})
        record = {
            "id": item_id,
            "namespace": namespace,
            "key": key,
            "value": copy.deepcopy(value),
            "metadata": copy.deepcopy(metadata or {}),
            "revision": previous.get("revision", 0) + 1,
            "created_at": previous.get("created_at", time.time()),
            "updated_at": time.time(),
        }
        self.items[item_id] = record
        self._log("updated" if exists else "stored", item_id)
        return {"ok": True, "created": not exists, "record": copy.deepcopy(record)}

    def get(self, namespace: str, key: str) -> Dict[str, Any]:
        item_id = self._item_id(namespace, key)
        record = self.items.get(item_id)
        if record is None:
            return {"ok": False, "error": "item_not_found", "id": item_id}
        return {"ok": True, "record": copy.deepcopy(record)}

    def list(self, namespace: Optional[str] = None) -> Dict[str, Any]:
        records = list(self.items.values())
        if namespace is not None:
            records = [record for record in records if record["namespace"] == namespace]
        return {"ok": True, "count": len(records), "records": copy.deepcopy(records)}

    def delete(self, namespace: str, key: str) -> Dict[str, Any]:
        item_id = self._item_id(namespace, key)
        record = self.items.pop(item_id, None)
        if record is None:
            return {"ok": False, "error": "item_not_found", "id": item_id}
        self._log("deleted", item_id)
        return {"ok": True, "deleted": item_id, "record": copy.deepcopy(record)}

    def status(self) -> Dict[str, Any]:
        by_namespace: Dict[str, int] = {}
        for record in self.items.values():
            by_namespace[record["namespace"]] = by_namespace.get(record["namespace"], 0) + 1
        return {"items": len(self.items), "history": len(self.history), "by_namespace": by_namespace}

    def _item_id(self, namespace: str, key: str) -> str:
        return f"{namespace}:{key}"

    def _log(self, action: str, item_id: str) -> None:
        entry = {"action": action, "id": item_id, "created_at": time.time()}
        self.history.append(entry)
        if self.kernel is not None and hasattr(self.kernel, "emit"):
            self.kernel.emit(f"runtime_storage.{action}", entry)

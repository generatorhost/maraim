import copy
import time
from typing import Any, Dict, List, Optional

from .runtime_object import RuntimeObject


class RuntimeObjectManager:
    """Object management foundation for RuntimeObjects.

    Provides create, update, clone, snapshot, restore, archive, and delete
    operations without hard-coding concrete object kinds.
    """

    def __init__(self, kernel: Any):
        self.kernel = kernel
        self.snapshots: Dict[str, List[Dict[str, Any]]] = {}
        self.archived: Dict[str, Dict[str, Any]] = {}
        self.history: List[Dict[str, Any]] = []

    def create(self, obj: RuntimeObject, connect: bool = False) -> Dict[str, Any]:
        if self.kernel.graph.get(obj.id) is not None:
            return {"ok": False, "error": "runtime_object_exists", "object_id": obj.id}
        obj.discover(self.kernel).validate(self.kernel).mount(self.kernel)
        self.kernel.graph.add_node(obj)
        if connect:
            obj.connect(self.kernel)
        self._record("create", obj.id, {"connect": connect})
        self.kernel.emit("object.created", {"object_id": obj.id, "kind": obj.kind})
        return {"ok": True, "object": obj.status()}

    def update(self, object_id: str, metadata: Optional[Dict[str, Any]] = None, capabilities: Optional[List[str]] = None) -> Dict[str, Any]:
        obj = self.kernel.graph.get(object_id)
        if obj is None:
            return {"ok": False, "error": "runtime_not_found", "object_id": object_id}
        if metadata:
            obj.metadata.update(metadata)
        if capabilities is not None:
            obj.capabilities = list(capabilities)
        self._record("update", object_id, {"metadata": metadata or {}, "capabilities": capabilities})
        self.kernel.emit("object.updated", {"object_id": object_id})
        return {"ok": True, "object": obj.status()}

    def clone(self, object_id: str, new_key: str, new_namespace: Optional[str] = None, new_version: Optional[str] = None) -> Dict[str, Any]:
        obj = self.kernel.graph.get(object_id)
        if obj is None:
            return {"ok": False, "error": "runtime_not_found", "object_id": object_id}
        cloned = copy.deepcopy(obj)
        cloned.namespace = new_namespace or obj.namespace
        cloned.key = new_key
        cloned.version = new_version or obj.version
        if self.kernel.graph.get(cloned.id) is not None:
            return {"ok": False, "error": "runtime_object_exists", "object_id": cloned.id}
        self.kernel.graph.add_node(cloned)
        self._record("clone", object_id, {"clone_id": cloned.id})
        self.kernel.emit("object.cloned", {"source_id": object_id, "clone_id": cloned.id})
        return {"ok": True, "source_id": object_id, "clone": cloned.status()}

    def snapshot(self, object_id: str, label: Optional[str] = None) -> Dict[str, Any]:
        obj = self.kernel.graph.get(object_id)
        if obj is None:
            return {"ok": False, "error": "runtime_not_found", "object_id": object_id}
        snapshot = {
            "id": f"snapshot:{object_id}:{len(self.snapshots.get(object_id, [])) + 1}",
            "object_id": object_id,
            "label": label,
            "timestamp": time.time(),
            "state": obj.status(),
        }
        self.snapshots.setdefault(object_id, []).append(snapshot)
        self._record("snapshot", object_id, {"snapshot_id": snapshot["id"]})
        self.kernel.emit("object.snapshotted", {"object_id": object_id, "snapshot_id": snapshot["id"]})
        return {"ok": True, "snapshot": snapshot}

    def restore(self, object_id: str, snapshot_id: Optional[str] = None) -> Dict[str, Any]:
        obj = self.kernel.graph.get(object_id)
        if obj is None:
            return {"ok": False, "error": "runtime_not_found", "object_id": object_id}
        snapshots = self.snapshots.get(object_id, [])
        if not snapshots:
            return {"ok": False, "error": "snapshot_not_found", "object_id": object_id}
        snapshot = next((s for s in snapshots if s["id"] == snapshot_id), snapshots[-1]) if snapshot_id else snapshots[-1]
        state = snapshot["state"]
        obj.metadata = dict(state.get("metadata", {}))
        obj.capabilities = list(state.get("capabilities", []))
        self._record("restore", object_id, {"snapshot_id": snapshot["id"]})
        self.kernel.emit("object.restored", {"object_id": object_id, "snapshot_id": snapshot["id"]})
        return {"ok": True, "object": obj.status(), "snapshot_id": snapshot["id"]}

    def archive(self, object_id: str) -> Dict[str, Any]:
        obj = self.kernel.graph.get(object_id)
        if obj is None:
            return {"ok": False, "error": "runtime_not_found", "object_id": object_id}
        self.archived[object_id] = {"object": obj.status(), "timestamp": time.time()}
        self._record("archive", object_id, {})
        self.kernel.emit("object.archived", {"object_id": object_id})
        return {"ok": True, "archived": self.archived[object_id]}

    def delete(self, object_id: str, archive: bool = True) -> Dict[str, Any]:
        obj = self.kernel.graph.get(object_id)
        if obj is None:
            return {"ok": False, "error": "runtime_not_found", "object_id": object_id}
        if archive:
            self.archive(object_id)
        removed = self.kernel.graph.remove_node(object_id)
        self._record("delete", object_id, {"archive": archive})
        self.kernel.emit("object.deleted", {"object_id": object_id, "removed": removed})
        return {"ok": True, "object_id": object_id, "removed": removed}

    def _record(self, action: str, object_id: str, data: Dict[str, Any]) -> None:
        self.history.append({"action": action, "object_id": object_id, "data": data, "timestamp": time.time()})

    def status(self) -> Dict[str, Any]:
        return {
            "objects": len(self.kernel.graph.nodes),
            "snapshots": sum(len(v) for v in self.snapshots.values()),
            "archived": len(self.archived),
            "history": len(self.history),
        }

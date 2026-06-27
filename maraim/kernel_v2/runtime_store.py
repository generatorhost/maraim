import copy
import time
from typing import Any, Dict, Iterable, List, Optional

from .runtime_object import RuntimeObject


class RuntimeStore:
    """In-memory RuntimeObject store for Kernel v2 foundation.

    The store is intentionally non-persistent in this phase: no DB writes, no
    API binding, and no filesystem mutation. It indexes RuntimeObjects already
    produced by DNA extraction, package import, or live DNA discovery so later
    phases can build mount, unmount, hot reload, and rollback behavior on a
    single clean registry surface.
    """

    def __init__(self, kernel: Any = None):
        self.kernel = kernel
        self.records: Dict[str, Dict[str, Any]] = {}
        self.snapshots: Dict[str, List[Dict[str, Any]]] = {}
        self.history: List[Dict[str, Any]] = []

    def put(self, obj: RuntimeObject, source: str = "runtime", mounted: Optional[bool] = None) -> Dict[str, Any]:
        exists = obj.id in self.records
        record = self._record_from_object(obj, source=source, mounted=mounted)
        previous = self.records.get(obj.id)
        if previous:
            record["created_at"] = previous.get("created_at", record["created_at"])
            record["revision"] = previous.get("revision", 0) + 1
        self.records[obj.id] = record
        self._index_graph_node(obj)
        self._log("updated" if exists else "stored", obj.id, {"source": source})
        return {"ok": True, "created": not exists, "record": copy.deepcopy(record)}

    def put_many(self, objects: Iterable[RuntimeObject], source: str = "runtime") -> Dict[str, Any]:
        stored = [self.put(obj, source=source)["record"]["id"] for obj in objects]
        return {"ok": True, "stored": stored, "count": len(stored)}

    def register_from_specs(self, specs: Iterable[Dict[str, Any]], source: str = "extracted") -> Dict[str, Any]:
        stored: List[str] = []
        for spec in specs:
            obj = self._object_from_spec(spec)
            stored.append(self.put(obj, source=source, mounted=self._is_mounted(obj.id))["record"]["id"])
        return {"ok": True, "stored": stored, "count": len(stored)}

    def sync_from_graph(self, source: str = "graph") -> Dict[str, Any]:
        if self.kernel is None:
            return {"ok": False, "error": "kernel_not_available"}
        return self.put_many(self.kernel.graph.nodes.values(), source=source)

    def get(self, runtime_id: str) -> Dict[str, Any]:
        record = self.records.get(runtime_id)
        if record is None:
            return {"ok": False, "error": "runtime_not_found", "runtime": runtime_id}
        return {"ok": True, "record": copy.deepcopy(record)}

    def list(
        self,
        kind: Optional[str] = None,
        capability: Optional[str] = None,
        source_path: Optional[str] = None,
        enabled: Optional[bool] = None,
        mounted: Optional[bool] = None,
    ) -> Dict[str, Any]:
        records = list(self.records.values())
        if kind is not None:
            records = [record for record in records if record.get("kind") == kind]
        if capability is not None:
            records = [record for record in records if capability in record.get("capabilities", [])]
        if source_path is not None:
            records = [record for record in records if record.get("source_path") == source_path]
        if enabled is not None:
            records = [record for record in records if record.get("enabled") is enabled]
        if mounted is not None:
            records = [record for record in records if record.get("mounted") is mounted]
        return {"ok": True, "count": len(records), "records": copy.deepcopy(records)}

    def enable(self, runtime_id: str, reason: str = "manual") -> Dict[str, Any]:
        return self._set_flag(runtime_id, "enabled", True, reason)

    def disable(self, runtime_id: str, reason: str = "manual") -> Dict[str, Any]:
        return self._set_flag(runtime_id, "enabled", False, reason)

    def mark_mounted(self, runtime_id: str, mounted: bool = True, reason: str = "mount_state") -> Dict[str, Any]:
        return self._set_flag(runtime_id, "mounted", mounted, reason)

    def mark_unmounted(self, runtime_id: str, reason: str = "unmount_state") -> Dict[str, Any]:
        return self.mark_mounted(runtime_id, mounted=False, reason=reason)

    def snapshot(self, runtime_id: str, label: str = "snapshot") -> Dict[str, Any]:
        record = self.records.get(runtime_id)
        if record is None:
            return {"ok": False, "error": "runtime_not_found", "runtime": runtime_id}
        item = {"label": label, "created_at": time.time(), "record": copy.deepcopy(record)}
        self.snapshots.setdefault(runtime_id, []).append(item)
        self._log("snapshot", runtime_id, {"label": label})
        return {"ok": True, "snapshot": copy.deepcopy(item), "count": len(self.snapshots[runtime_id])}

    def restore(self, runtime_id: str, index: int = -1) -> Dict[str, Any]:
        items = self.snapshots.get(runtime_id, [])
        if not items:
            return {"ok": False, "error": "snapshot_not_found", "runtime": runtime_id}
        try:
            restored = copy.deepcopy(items[index]["record"])
        except IndexError:
            return {"ok": False, "error": "snapshot_index_not_found", "runtime": runtime_id, "index": index}
        restored["revision"] = self.records.get(runtime_id, {}).get("revision", 0) + 1
        restored["updated_at"] = time.time()
        self.records[runtime_id] = restored
        self._log("restored", runtime_id, {"index": index})
        return {"ok": True, "record": copy.deepcopy(restored)}

    def remove(self, runtime_id: str, reason: str = "removed") -> Dict[str, Any]:
        record = self.records.pop(runtime_id, None)
        if record is None:
            return {"ok": False, "error": "runtime_not_found", "runtime": runtime_id}
        self._log("removed", runtime_id, {"reason": reason})
        return {"ok": True, "removed": runtime_id, "record": copy.deepcopy(record)}

    def status(self) -> Dict[str, Any]:
        by_kind: Dict[str, int] = {}
        by_source: Dict[str, int] = {}
        capability_index: Dict[str, int] = {}
        enabled = 0
        mounted = 0
        for record in self.records.values():
            by_kind[record["kind"]] = by_kind.get(record["kind"], 0) + 1
            by_source[record["source"]] = by_source.get(record["source"], 0) + 1
            enabled += 1 if record.get("enabled") else 0
            mounted += 1 if record.get("mounted") else 0
            for capability in record.get("capabilities", []):
                capability_index[capability] = capability_index.get(capability, 0) + 1
        return {
            "runtimes": len(self.records),
            "enabled": enabled,
            "disabled": len(self.records) - enabled,
            "mounted": mounted,
            "snapshots": sum(len(items) for items in self.snapshots.values()),
            "history": len(self.history),
            "by_kind": by_kind,
            "by_source": by_source,
            "capabilities": capability_index,
        }

    def _record_from_object(self, obj: RuntimeObject, source: str, mounted: Optional[bool] = None) -> Dict[str, Any]:
        now = time.time()
        return {
            "id": obj.id,
            "namespace": obj.namespace,
            "key": obj.key,
            "version": obj.version,
            "kind": obj.kind,
            "state": obj.state.value if hasattr(obj.state, "value") else str(obj.state),
            "capabilities": list(obj.capabilities),
            "metadata": copy.deepcopy(obj.metadata),
            "source": source,
            "source_path": obj.metadata.get("source_path"),
            "enabled": True,
            "mounted": self._is_mounted(obj.id) if mounted is None else bool(mounted),
            "revision": 1,
            "created_at": now,
            "updated_at": now,
        }

    def _object_from_spec(self, spec: Dict[str, Any]) -> RuntimeObject:
        namespace, key, version = self._parse_id(spec.get("id", "runtime.unknown@1.0.0"))
        metadata = dict(spec.get("metadata", {}))
        metadata["source_path"] = spec.get("source_path")
        metadata["stored_from_spec"] = True
        return RuntimeObject(
            namespace=namespace,
            key=key,
            version=version,
            kind=spec.get("kind", "runtime"),
            capabilities=list(spec.get("capabilities", [])),
            metadata=metadata,
        )

    def _parse_id(self, value: str) -> tuple[str, str, str]:
        raw = value or "runtime.unknown@1.0.0"
        version = "1.0.0"
        if "@" in raw:
            raw, version = raw.rsplit("@", 1)
        if "." in raw:
            namespace, key = raw.rsplit(".", 1)
        else:
            namespace, key = "runtime", raw
        return namespace, key, version

    def _set_flag(self, runtime_id: str, flag: str, value: bool, reason: str) -> Dict[str, Any]:
        record = self.records.get(runtime_id)
        if record is None:
            return {"ok": False, "error": "runtime_not_found", "runtime": runtime_id}
        record[flag] = value
        record["revision"] = record.get("revision", 0) + 1
        record["updated_at"] = time.time()
        self._log(flag, runtime_id, {"value": value, "reason": reason})
        return {"ok": True, "record": copy.deepcopy(record)}

    def _index_graph_node(self, obj: RuntimeObject) -> None:
        if self.kernel is None:
            return
        if self.kernel.graph.get(obj.id) is None:
            self.kernel.graph.add_node(obj)

    def _is_mounted(self, runtime_id: str) -> bool:
        if self.kernel is None:
            return False
        return self.kernel.graph.get(runtime_id) is not None

    def _log(self, action: str, runtime_id: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        item = {"action": action, "runtime": runtime_id, "metadata": metadata or {}, "created_at": time.time()}
        self.history.append(item)
        if self.kernel is not None and hasattr(self.kernel, "emit"):
            self.kernel.emit(f"runtime_store.{action}", item)

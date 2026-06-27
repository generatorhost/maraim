import time
from typing import Any, Dict, List, Optional

from .runtime_store import RuntimeStore


class RuntimeMountManager:
    """Mount/Unmount foundation for RuntimeObjects.

    This manager coordinates mount state in RuntimeStore and RuntimeGraph without
    loading modules, writing files, calling APIs, or touching a database. It is a
    deterministic control surface for later lifecycle-safe remount, hot reload,
    and package mount behavior.
    """

    def __init__(self, kernel: Any, store: Optional[RuntimeStore] = None):
        self.kernel = kernel
        self.store = store or RuntimeStore(kernel)
        self.operations: List[Dict[str, Any]] = []

    def mount(self, runtime_id: str, reason: str = "manual_mount") -> Dict[str, Any]:
        record = self.store.get(runtime_id)
        if not record.get("ok"):
            return record
        result = self.store.mark_mounted(runtime_id, mounted=True, reason=reason)
        self._log("mount", runtime_id, {"reason": reason, "ok": result.get("ok")})
        return {"ok": result.get("ok", False), "runtime": runtime_id, "record": result.get("record")}

    def unmount(self, runtime_id: str, reason: str = "manual_unmount") -> Dict[str, Any]:
        record = self.store.get(runtime_id)
        if not record.get("ok"):
            return record
        result = self.store.mark_unmounted(runtime_id, reason=reason)
        self._log("unmount", runtime_id, {"reason": reason, "ok": result.get("ok")})
        return {"ok": result.get("ok", False), "runtime": runtime_id, "record": result.get("record")}

    def remount(self, runtime_id: str, reason: str = "manual_remount") -> Dict[str, Any]:
        before = self.unmount(runtime_id, reason=f"{reason}:before")
        if not before.get("ok"):
            return before
        after = self.mount(runtime_id, reason=f"{reason}:after")
        self._log("remount", runtime_id, {"reason": reason, "ok": after.get("ok")})
        return {"ok": after.get("ok", False), "runtime": runtime_id, "before": before, "after": after}

    def mount_by_kind(self, kind: str, reason: str = "kind_mount") -> Dict[str, Any]:
        items = self.store.list(kind=kind)
        mounted = [self.mount(record["id"], reason=reason) for record in items.get("records", [])]
        return {"ok": all(item.get("ok") for item in mounted), "kind": kind, "mounted": mounted, "count": len(mounted)}

    def unmount_by_kind(self, kind: str, reason: str = "kind_unmount") -> Dict[str, Any]:
        items = self.store.list(kind=kind)
        unmounted = [self.unmount(record["id"], reason=reason) for record in items.get("records", [])]
        return {"ok": all(item.get("ok") for item in unmounted), "kind": kind, "unmounted": unmounted, "count": len(unmounted)}

    def mount_by_capability(self, capability: str, reason: str = "capability_mount") -> Dict[str, Any]:
        items = self.store.list(capability=capability)
        mounted = [self.mount(record["id"], reason=reason) for record in items.get("records", [])]
        return {"ok": all(item.get("ok") for item in mounted), "capability": capability, "mounted": mounted, "count": len(mounted)}

    def unmount_by_capability(self, capability: str, reason: str = "capability_unmount") -> Dict[str, Any]:
        items = self.store.list(capability=capability)
        unmounted = [self.unmount(record["id"], reason=reason) for record in items.get("records", [])]
        return {"ok": all(item.get("ok") for item in unmounted), "capability": capability, "unmounted": unmounted, "count": len(unmounted)}

    def status(self) -> Dict[str, Any]:
        store_status = self.store.status()
        return {
            "operations": len(self.operations),
            "mounted": store_status.get("mounted", 0),
            "runtimes": store_status.get("runtimes", 0),
            "last": self.operations[-1] if self.operations else None,
        }

    def _log(self, action: str, runtime_id: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        item = {"action": action, "runtime": runtime_id, "metadata": metadata or {}, "created_at": time.time()}
        self.operations.append(item)
        if hasattr(self.kernel, "emit"):
            self.kernel.emit(f"runtime_mount.{action}", item)

import time
from typing import Any, Dict, Optional


class RuntimeSnapshotBuilder:
    """In-memory runtime snapshot foundation for Kernel v2."""

    def __init__(self, kernel: Any = None):
        self.kernel = kernel
        self.snapshots: Dict[str, Dict[str, Any]] = {}

    def build_snapshot(
        self,
        label: str,
        store_status: Optional[Dict[str, Any]] = None,
        execution_status: Optional[Dict[str, Any]] = None,
        artifact_status: Optional[Dict[str, Any]] = None,
        audit_status: Optional[Dict[str, Any]] = None,
        metrics_status: Optional[Dict[str, Any]] = None,
        trace_status: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        snapshot_id = f"snapshot:{len(self.snapshots) + 1}"
        snapshot = {
            "id": snapshot_id,
            "label": label,
            "store": store_status or {},
            "execution": execution_status or {},
            "artifacts": artifact_status or {},
            "audit": audit_status or {},
            "metrics": metrics_status or {},
            "trace": trace_status or {},
            "created_at": time.time(),
        }
        self.snapshots[snapshot_id] = snapshot
        if self.kernel is not None and hasattr(self.kernel, "emit"):
            self.kernel.emit("runtime_snapshot.created", snapshot)
        return {"ok": True, "snapshot": snapshot}

    def compare(self, before_id: str, after_id: str) -> Dict[str, Any]:
        before = self.snapshots.get(before_id)
        after = self.snapshots.get(after_id)
        if before is None or after is None:
            return {"ok": False, "error": "snapshot_not_found", "before": before_id, "after": after_id}
        diff = {}
        for key in ["store", "execution", "artifacts", "audit", "metrics", "trace"]:
            diff[key] = {"before": before.get(key, {}), "after": after.get(key, {})}
        return {"ok": True, "before": before_id, "after": after_id, "diff": diff}

    def get(self, snapshot_id: str) -> Dict[str, Any]:
        snapshot = self.snapshots.get(snapshot_id)
        if snapshot is None:
            return {"ok": False, "error": "snapshot_not_found", "snapshot": snapshot_id}
        return {"ok": True, "snapshot": snapshot}

    def status(self) -> Dict[str, Any]:
        return {"snapshots": len(self.snapshots), "last": list(self.snapshots.values())[-1] if self.snapshots else None}

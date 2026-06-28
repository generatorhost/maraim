import time
from typing import Any, Dict, List


class PersistenceStatus:
    """Small status helper for persistence bridges."""

    def __init__(self, kernel: Any = None):
        self.kernel = kernel
        self.items: List[Dict[str, Any]] = []

    def audit_bridge_status(self, bridge: Any, label: str = "audit") -> Dict[str, Any]:
        sync = bridge.verify_sync()
        item = {"label": label, "ok": bool(sync.get("in_sync")), "sync": sync, "created_at": time.time()}
        self.items.append(item)
        if self.kernel is not None and hasattr(self.kernel, "emit"):
            self.kernel.emit("persistence_status.audit_bridge", item)
        return {"ok": True, "item": item}

    def status(self) -> Dict[str, Any]:
        failed = [item for item in self.items if not item["ok"]]
        return {"ok": not failed, "checks": len(self.items), "failed": failed, "last": self.items[-1] if self.items else None}

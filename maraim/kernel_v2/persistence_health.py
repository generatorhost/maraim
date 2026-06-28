import time
from typing import Any, Dict, List


class PersistenceHealth:
    """Health checks for persistence bridges."""

    def __init__(self, kernel: Any = None):
        self.kernel = kernel
        self.checks: List[Dict[str, Any]] = []

    def audit_bridge_health(self, bridge: Any, label: str = "audit") -> Dict[str, Any]:
        sync = bridge.verify_sync()
        health = "ready" if sync.get("in_sync") else "degraded"
        check = {"label": label, "ok": health == "ready", "health": health, "sync": sync, "created_at": time.time()}
        self.checks.append(check)
        if self.kernel is not None and hasattr(self.kernel, "emit"):
            self.kernel.emit("persistence_health.audit_bridge", check)
        return {"ok": True, "check": check}

    def status(self) -> Dict[str, Any]:
        failed = [item for item in self.checks if not item["ok"]]
        return {"ok": not failed, "checks": len(self.checks), "failed": failed, "last": self.checks[-1] if self.checks else None}

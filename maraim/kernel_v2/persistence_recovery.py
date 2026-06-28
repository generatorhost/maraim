import time
from typing import Any, Dict, List


class PersistenceRecovery:
    """Recovery planner for persistence bridges."""

    def __init__(self, kernel: Any = None):
        self.kernel = kernel
        self.actions: List[Dict[str, Any]] = []

    def inspect_audit_bridge(self, bridge: Any, label: str = "audit") -> Dict[str, Any]:
        sync = bridge.verify_sync()
        gap = sync.get("audit_events", 0) - sync.get("persisted_events", 0)
        action = "none" if sync.get("in_sync") else "flush_new"
        plan = {"label": label, "action": action, "gap": gap, "sync": sync, "created_at": time.time()}
        self.actions.append(plan)
        if self.kernel is not None and hasattr(self.kernel, "emit"):
            self.kernel.emit("persistence_recovery.inspected", plan)
        return {"ok": True, "plan": plan}

    def recover_audit_bridge(self, bridge: Any, label: str = "audit") -> Dict[str, Any]:
        inspection = self.inspect_audit_bridge(bridge, label)
        if inspection["plan"]["action"] == "none":
            return {"ok": True, "recovered": False, "inspection": inspection["plan"], "result": {"count": 0}}
        result = bridge.flush_new()
        after = bridge.verify_sync()
        return {"ok": bool(after.get("in_sync")), "recovered": True, "inspection": inspection["plan"], "result": result, "after": after}

    def status(self) -> Dict[str, Any]:
        return {"ok": True, "actions": len(self.actions), "last": self.actions[-1] if self.actions else None}

import time
from typing import Any, Dict, List


class PersistenceCheckpoint:
    """In-memory checkpoints for persistence bridge state."""

    def __init__(self, kernel: Any = None):
        self.kernel = kernel
        self.checkpoints: List[Dict[str, Any]] = []

    def capture_audit_bridge(self, bridge: Any, label: str = "audit") -> Dict[str, Any]:
        sync = bridge.verify_sync()
        checkpoint = {"id": f"persistence_checkpoint:{len(self.checkpoints) + 1}", "label": label, "sync": sync, "created_at": time.time()}
        self.checkpoints.append(checkpoint)
        if self.kernel is not None and hasattr(self.kernel, "emit"):
            self.kernel.emit("persistence_checkpoint.captured", checkpoint)
        return {"ok": True, "checkpoint": checkpoint}

    def compare(self, before_id: str, after_id: str) -> Dict[str, Any]:
        before = self._find(before_id)
        after = self._find(after_id)
        if before is None or after is None:
            return {"ok": False, "error": "checkpoint_not_found", "before": before_id, "after": after_id}
        return {"ok": True, "before": before, "after": after, "changed": before.get("sync") != after.get("sync")}

    def status(self) -> Dict[str, Any]:
        return {"ok": True, "checkpoints": len(self.checkpoints), "last": self.checkpoints[-1] if self.checkpoints else None}

    def _find(self, checkpoint_id: str):
        for checkpoint in self.checkpoints:
            if checkpoint["id"] == checkpoint_id:
                return checkpoint
        return None

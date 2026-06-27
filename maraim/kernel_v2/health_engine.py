import time
from typing import Any, Dict, List


class RuntimeHealthEngine:
    """Small in-memory health checker for Kernel v2 layers."""

    def __init__(self, kernel: Any = None):
        self.kernel = kernel
        self.checks: List[Dict[str, Any]] = []

    def record(self, name: str, ok: bool, details: Dict[str, Any]) -> Dict[str, Any]:
        item = {"name": name, "ok": bool(ok), "details": dict(details), "created_at": time.time()}
        self.checks.append(item)
        if self.kernel is not None and hasattr(self.kernel, "emit"):
            self.kernel.emit(f"runtime_health.{name}", item)
        return item

    def check_counter(self, name: str, value: int, minimum: int = 0) -> Dict[str, Any]:
        return self.record(name, value >= minimum, {"value": value, "minimum": minimum})

    def summary(self) -> Dict[str, Any]:
        failed = [item for item in self.checks if not item["ok"]]
        return {"ok": not failed, "checks": len(self.checks), "failed": failed, "last": self.checks[-1] if self.checks else None}

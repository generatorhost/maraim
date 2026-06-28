import time
from typing import Any, Dict, Iterable, List


BRIDGE_STEPS = [
    "source_readiness",
    "safety_policy",
    "permission_profile",
    "request_record",
    "approval_record",
    "dry_run_record",
    "rollback_record",
    "diagnostic_record",
    "promotion_report",
    "completion_update",
]


class ProductionBridgeSteps:
    """Ten small records for moving from foundation toward production."""

    def __init__(self, kernel: Any = None):
        self.kernel = kernel
        self.records: List[Dict[str, Any]] = []

    def add(self, step: str, label: str, ok: bool = True, details: Dict[str, Any] | None = None) -> Dict[str, Any]:
        if step not in BRIDGE_STEPS:
            return {"ok": False, "error": "step_not_allowed", "step": step}
        record = {"step": step, "label": label, "ok": bool(ok), "details": details or {}, "created_at": time.time()}
        self.records.append(record)
        if self.kernel is not None and hasattr(self.kernel, "emit"):
            self.kernel.emit("production_bridge.record", record)
        return {"ok": True, "record": record}

    def complete_default_path(self, label: str = "production-bridge") -> Dict[str, Any]:
        results = [self.add(step, label, True, {"mode": "record_only"}) for step in BRIDGE_STEPS]
        return {"ok": all(item["ok"] for item in results), "results": results, "summary": self.summary()}

    def summary(self) -> Dict[str, Any]:
        total = len(BRIDGE_STEPS)
        passed = len([item for item in self.records if item["ok"]])
        seen = sorted(set(item["step"] for item in self.records))
        complete = all(step in seen for step in BRIDGE_STEPS)
        percent = round((len(seen) / total) * 100, 2)
        return {"ok": complete, "steps": total, "seen": len(seen), "passed": passed, "percent": percent, "complete": complete}

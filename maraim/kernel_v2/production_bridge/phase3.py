import time
from typing import Any, Dict, List


PHASE3_STEPS = [
    "execution_window",
    "operator_hold",
    "preflight_result",
    "sandbox_receipt",
    "permission_receipt",
    "artifact_receipt",
    "rollback_receipt",
    "health_receipt",
    "promotion_decision",
    "post_run_review",
]


class ProductionBridgePhase3:
    """Third set of ten production bridge control records."""

    def __init__(self, kernel: Any = None):
        self.kernel = kernel
        self.records: List[Dict[str, Any]] = []

    def add(self, step: str, ok: bool = True) -> Dict[str, Any]:
        if step not in PHASE3_STEPS:
            return {"ok": False, "error": "step_not_allowed", "step": step}
        record = {"step": step, "ok": bool(ok), "created_at": time.time()}
        self.records.append(record)
        if self.kernel is not None and hasattr(self.kernel, "emit"):
            self.kernel.emit("production_bridge.phase3", record)
        return {"ok": True, "record": record}

    def complete(self) -> Dict[str, Any]:
        results = [self.add(step, True) for step in PHASE3_STEPS]
        return {"ok": all(item["ok"] for item in results), "summary": self.summary(), "results": results}

    def summary(self) -> Dict[str, Any]:
        seen = set(item["step"] for item in self.records)
        percent = round((len(seen) / len(PHASE3_STEPS)) * 100, 2)
        return {"ok": len(seen) == len(PHASE3_STEPS), "total": len(PHASE3_STEPS), "seen": len(seen), "percent": percent}

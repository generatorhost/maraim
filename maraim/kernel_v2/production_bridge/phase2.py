import time
from typing import Any, Dict, List


PHASE2_STEPS = [
    "input_contract",
    "output_contract",
    "side_effect_policy",
    "timeout_policy",
    "resource_budget",
    "audit_binding",
    "metrics_binding",
    "trace_binding",
    "checkpoint_binding",
    "recovery_binding",
]


class ProductionBridgePhase2:
    """Second set of ten production bridge records."""

    def __init__(self, kernel: Any = None):
        self.kernel = kernel
        self.records: List[Dict[str, Any]] = []

    def add(self, step: str, ok: bool = True) -> Dict[str, Any]:
        if step not in PHASE2_STEPS:
            return {"ok": False, "error": "step_not_allowed", "step": step}
        record = {"step": step, "ok": bool(ok), "created_at": time.time()}
        self.records.append(record)
        if self.kernel is not None and hasattr(self.kernel, "emit"):
            self.kernel.emit("production_bridge.phase2", record)
        return {"ok": True, "record": record}

    def complete(self) -> Dict[str, Any]:
        results = [self.add(step, True) for step in PHASE2_STEPS]
        return {"ok": all(item["ok"] for item in results), "summary": self.summary(), "results": results}

    def summary(self) -> Dict[str, Any]:
        seen = set(item["step"] for item in self.records)
        percent = round((len(seen) / len(PHASE2_STEPS)) * 100, 2)
        return {"ok": len(seen) == len(PHASE2_STEPS), "total": len(PHASE2_STEPS), "seen": len(seen), "percent": percent}

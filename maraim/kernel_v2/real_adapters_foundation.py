import time
from typing import Any, Dict, Iterable, List, Optional


class RealAdapterFoundation:
    """Safe foundation for real source adapters.

    This is not a real clone/extract/scan implementation yet. It defines
    validation and execution plans for Git, archive, and folder adapters so real
    adapters can be added later behind explicit guards.
    """

    allowed_adapter_types = {"git", "archive", "folder"}

    def __init__(self, kernel: Any = None):
        self.kernel = kernel
        self.adapters: Dict[str, Dict[str, Any]] = {}
        self.plans: Dict[str, Dict[str, Any]] = {}

    def register_adapter(self, adapter_id: str, adapter_type: str, capabilities: Iterable[str], safety: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        adapter_type = adapter_type.strip().lower()
        if adapter_type not in self.allowed_adapter_types:
            return {"ok": False, "error": "adapter_type_not_allowed", "adapter_type": adapter_type}
        adapter = {
            "id": adapter_id,
            "type": adapter_type,
            "capabilities": sorted(set(capabilities)),
            "safety": safety or {"mode": "plan_only", "network": False, "filesystem_write": False, "subprocess": False},
            "created_at": time.time(),
        }
        self.adapters[adapter_id] = adapter
        self._emit("registered", adapter)
        return {"ok": True, "adapter": adapter}

    def validate_adapter(self, adapter_id: str, required_capabilities: Iterable[str]) -> Dict[str, Any]:
        adapter = self.adapters.get(adapter_id)
        if adapter is None:
            return {"ok": False, "error": "adapter_not_found", "adapter": adapter_id}
        missing = [item for item in required_capabilities if item not in adapter["capabilities"]]
        unsafe = [key for key, value in adapter.get("safety", {}).items() if key in {"network", "filesystem_write", "subprocess"} and value]
        return {"ok": not missing and not unsafe, "adapter": adapter, "missing": missing, "unsafe": unsafe}

    def build_plan(self, plan_id: str, adapter_id: str, source: str, operations: Iterable[str]) -> Dict[str, Any]:
        validation = self.validate_adapter(adapter_id, operations)
        plan = {
            "id": plan_id,
            "adapter_id": adapter_id,
            "source": source,
            "operations": list(operations),
            "validation": validation,
            "mode": "foundation_plan_only",
            "can_execute": validation.get("ok", False),
            "created_at": time.time(),
        }
        self.plans[plan_id] = plan
        self._emit("planned", plan)
        return {"ok": True, "plan": plan}

    def readiness(self) -> Dict[str, Any]:
        ready = [item for item in self.plans.values() if item.get("can_execute")]
        blocked = [item for item in self.plans.values() if not item.get("can_execute")]
        return {"ok": True, "adapters": len(self.adapters), "plans": len(self.plans), "ready": len(ready), "blocked": len(blocked)}

    def status(self) -> Dict[str, Any]:
        by_type: Dict[str, int] = {}
        for adapter in self.adapters.values():
            by_type[adapter["type"]] = by_type.get(adapter["type"], 0) + 1
        return {"adapters": len(self.adapters), "plans": len(self.plans), "by_type": by_type}

    def _emit(self, suffix: str, payload: Dict[str, Any]) -> None:
        if self.kernel is not None and hasattr(self.kernel, "emit"):
            self.kernel.emit(f"real_adapter_foundation.{suffix}", payload)

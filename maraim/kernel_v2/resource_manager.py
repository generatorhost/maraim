import time
from typing import Any, Dict, List, Optional


class RuntimeResourceManager:
    """Resource allocation foundation for RuntimeObjects.

    The manager tracks logical resources without knowing concrete runtime kinds.
    It can allocate CPU/RAM/GPU/VRAM/disk/network/thread budgets to any
    RuntimeObject identity and release or rebalance them later.
    """

    DEFAULT_CAPACITY = {
        "cpu_units": 100,
        "ram_mb": 8192,
        "gpu_units": 0,
        "vram_mb": 0,
        "disk_mb": 102400,
        "network_units": 100,
        "threads": 32,
    }

    def __init__(self, kernel: Any, capacity: Optional[Dict[str, int]] = None):
        self.kernel = kernel
        self.capacity: Dict[str, int] = dict(self.DEFAULT_CAPACITY)
        if capacity:
            self.capacity.update({k: int(v) for k, v in capacity.items()})
        self.allocations: Dict[str, Dict[str, Any]] = {}
        self.history: List[Dict[str, Any]] = []

    def available(self) -> Dict[str, int]:
        used = self.used()
        return {key: self.capacity.get(key, 0) - used.get(key, 0) for key in self.capacity}

    def used(self) -> Dict[str, int]:
        totals = {key: 0 for key in self.capacity}
        for allocation in self.allocations.values():
            resources = allocation.get("resources", {})
            for key in totals:
                totals[key] += int(resources.get(key, 0))
        return totals

    def can_allocate(self, resources: Dict[str, int]) -> Dict[str, Any]:
        available = self.available()
        blocked = {
            key: {"requested": int(value), "available": available.get(key, 0)}
            for key, value in resources.items()
            if int(value) > available.get(key, 0)
        }
        return {"ok": not blocked, "blocked": blocked, "available": available}

    def allocate(self, object_id: str, resources: Optional[Dict[str, int]] = None, reason: Optional[str] = None) -> Dict[str, Any]:
        if self.kernel.graph.get(object_id) is None:
            return {"ok": False, "error": "runtime_not_found", "object_id": object_id}
        resources = {k: int(v) for k, v in (resources or {}).items() if int(v) >= 0}
        check = self.can_allocate(resources)
        if not check.get("ok"):
            return {"ok": False, "error": "insufficient_resources", "object_id": object_id, **check}
        record = {
            "object_id": object_id,
            "resources": resources,
            "reason": reason,
            "created_at": time.time(),
            "updated_at": time.time(),
        }
        self.allocations[object_id] = record
        self.history.append({"action": "allocate", "record": dict(record), "timestamp": time.time()})
        self.kernel.emit("resource.allocated", {"object_id": object_id, "resources": resources})
        return {"ok": True, "allocation": record, "available": self.available()}

    def release(self, object_id: str) -> Dict[str, Any]:
        record = self.allocations.pop(object_id, None)
        if record is None:
            return {"ok": False, "error": "allocation_not_found", "object_id": object_id}
        self.history.append({"action": "release", "record": dict(record), "timestamp": time.time()})
        self.kernel.emit("resource.released", {"object_id": object_id, "resources": record.get("resources", {})})
        return {"ok": True, "released": record, "available": self.available()}

    def rebalance(self) -> Dict[str, Any]:
        """Foundation hook for future intelligent resource redistribution."""
        snapshot = {
            "capacity": dict(self.capacity),
            "used": self.used(),
            "available": self.available(),
            "allocations": list(self.allocations.values()),
        }
        self.history.append({"action": "rebalance", "snapshot": snapshot, "timestamp": time.time()})
        self.kernel.emit("resource.rebalanced", snapshot)
        return {"ok": True, "snapshot": snapshot}

    def status(self) -> Dict[str, Any]:
        return {
            "capacity": dict(self.capacity),
            "used": self.used(),
            "available": self.available(),
            "allocations": len(self.allocations),
            "history": len(self.history),
        }

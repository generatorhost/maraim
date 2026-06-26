import time
from typing import Any, Dict, List, Optional


class RuntimeLifecycleManager:
    """Lifecycle and health manager for RuntimeObjects.

    This manager keeps the Kernel small: it does not know Agent, Model,
    Mission, Plugin, or Swarm. It tracks RuntimeObject identities and state.
    """

    VALID_STATES = {
        "discovered",
        "validated",
        "mounted",
        "connected",
        "ready",
        "busy",
        "idle",
        "scaling",
        "paused",
        "stopping",
        "retired",
        "error",
    }

    def __init__(self, kernel: Any):
        self.kernel = kernel
        self.records: Dict[str, Dict[str, Any]] = {}
        self.transitions: List[Dict[str, Any]] = []

    def register_graph(self) -> Dict[str, Any]:
        registered = []
        for object_id, obj in self.kernel.graph.nodes.items():
            self.register(obj)
            registered.append(object_id)
        return {"ok": True, "registered": registered, "count": len(registered)}

    def register(self, obj: Any, state: str = "ready") -> Dict[str, Any]:
        object_id = obj.id
        now = time.time()
        self.records[object_id] = {
            "id": object_id,
            "kind": getattr(obj, "kind", "runtime"),
            "state": state,
            "created_at": now,
            "updated_at": now,
            "heartbeat_at": now,
            "health": {
                "ok": True,
                "errors": 0,
                "latency_ms": 0,
                "load": 0,
                "queue": 0,
                "uptime_ms": 0,
            },
        }
        self.kernel.emit("lifecycle.registered", {"object_id": object_id, "state": state})
        return {"ok": True, "record": self.records[object_id]}

    def transition(self, object_id: str, state: str, reason: Optional[str] = None) -> Dict[str, Any]:
        if state not in self.VALID_STATES:
            return {"ok": False, "error": "invalid_lifecycle_state", "state": state}
        if object_id not in self.records:
            obj = self.kernel.graph.get(object_id)
            if obj is None:
                return {"ok": False, "error": "runtime_not_found", "object_id": object_id}
            self.register(obj)
        previous = self.records[object_id]["state"]
        self.records[object_id]["state"] = state
        self.records[object_id]["updated_at"] = time.time()
        transition = {
            "object_id": object_id,
            "from": previous,
            "to": state,
            "reason": reason,
            "timestamp": time.time(),
        }
        self.transitions.append(transition)
        self.kernel.emit("lifecycle.transitioned", transition)
        return {"ok": True, "transition": transition}

    def heartbeat(self, object_id: str, **health: Any) -> Dict[str, Any]:
        if object_id not in self.records:
            obj = self.kernel.graph.get(object_id)
            if obj is None:
                return {"ok": False, "error": "runtime_not_found", "object_id": object_id}
            self.register(obj)
        now = time.time()
        record = self.records[object_id]
        record["heartbeat_at"] = now
        record["updated_at"] = now
        record["health"].update(health)
        record["health"]["uptime_ms"] = int((now - record["created_at"]) * 1000)
        self.kernel.emit("lifecycle.heartbeat", {"object_id": object_id, "health": record["health"]})
        return {"ok": True, "record": record}

    def mark_error(self, object_id: str, error: str) -> Dict[str, Any]:
        if object_id not in self.records:
            obj = self.kernel.graph.get(object_id)
            if obj is None:
                return {"ok": False, "error": "runtime_not_found", "object_id": object_id}
            self.register(obj)
        self.records[object_id]["health"]["ok"] = False
        self.records[object_id]["health"]["errors"] += 1
        self.records[object_id]["health"]["last_error"] = error
        return self.transition(object_id, "error", reason=error)

    def recover(self, object_id: str, strategy: str = "reload") -> Dict[str, Any]:
        if object_id not in self.records:
            return {"ok": False, "error": "runtime_not_registered", "object_id": object_id}
        self.records[object_id]["health"]["ok"] = True
        result = self.transition(object_id, "ready", reason=f"recovered:{strategy}")
        self.kernel.emit("lifecycle.recovered", {"object_id": object_id, "strategy": strategy})
        return result

    def status(self) -> Dict[str, Any]:
        counts: Dict[str, int] = {}
        for record in self.records.values():
            counts[record["state"]] = counts.get(record["state"], 0) + 1
        return {
            "runtimes": len(self.records),
            "states": counts,
            "transitions": len(self.transitions),
            "healthy": sum(1 for r in self.records.values() if r["health"].get("ok") is True),
            "unhealthy": sum(1 for r in self.records.values() if r["health"].get("ok") is not True),
        }

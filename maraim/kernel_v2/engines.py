from typing import Any, Dict, List, Optional

from .dna_manager import DNAManager
from .runtime_graph import RuntimeGraph
from .runtime_object import RuntimeObject


class ObjectEngine:
    def __init__(self, graph: RuntimeGraph):
        self.graph = graph

    def register(self, obj: RuntimeObject) -> RuntimeObject:
        return self.graph.add_node(obj)

    def get(self, object_id: str) -> RuntimeObject | None:
        return self.graph.get(object_id)


class ResourceEngine:
    def __init__(self, graph: RuntimeGraph):
        self.graph = graph

    def resolve_capability(self, capability: str) -> Dict[str, Any]:
        matches = self.graph.find_by_capability(capability)
        if not matches:
            return {"ok": False, "error": "capability_not_found", "capability": capability}
        return {"ok": True, "capability": capability, "runtime": matches[0].status(), "candidates": [m.id for m in matches]}


class ExecutionEngine:
    """Graph-based execution foundation.

    Executes a RuntimeObject and its outgoing graph relations without the
    Kernel knowing concrete types such as Mission, Agent, Model, or Swarm.
    """

    EXECUTABLE_RELATIONS = {
        "uses_agent",
        "uses_model",
        "uses_swarm",
        "uses_tool",
        "uses_plugin",
        "uses_skill",
        "uses_capability",
        "uses_service",
    }

    def __init__(self, kernel: "KernelV2"):
        self.kernel = kernel
        self.runs: List[Dict[str, Any]] = []

    def execute(self, object_id: str, payload: Optional[Dict[str, Any]] = None, depth: int = 1) -> Dict[str, Any]:
        payload = payload or {}
        obj = self.kernel.graph.get(object_id)
        if obj is None:
            return {"ok": False, "error": "runtime_not_found", "object_id": object_id}

        result = {
            "ok": True,
            "object": obj.status(),
            "result": obj.execute(payload),
            "children": [],
        }

        if depth > 0:
            for edge in self.kernel.graph.outgoing(object_id):
                if edge.relation not in self.EXECUTABLE_RELATIONS:
                    continue
                child = self.kernel.graph.get(edge.target)
                if child is None:
                    result["children"].append({"ok": False, "edge": edge.__dict__, "error": "target_not_found"})
                    continue
                child_payload = {"parent": object_id, "relation": edge.relation, "payload": payload}
                result["children"].append({
                    "ok": True,
                    "relation": edge.relation,
                    "target": child.status(),
                    "result": child.execute(child_payload),
                })

        self.runs.append(result)
        self.kernel.emit("execution.completed", {"object_id": object_id, "children": len(result["children"])})
        return result

    def status(self) -> Dict[str, Any]:
        return {"runs": len(self.runs), "last": self.runs[-1] if self.runs else None}


class DiagnosticsEngine:
    def __init__(self, kernel: "KernelV2"):
        self.kernel = kernel

    def status(self) -> Dict[str, Any]:
        return self.kernel.status()


class KernelV2:
    """Small Kernel host for unlimited DNA RuntimeObjects.

    This is an additive, non-breaking v2 foundation. It does not replace the
    existing Kernel2 runtime yet.
    """

    def __init__(self, dna_root: str = "dna"):
        self.graph = RuntimeGraph()
        self.dna = DNAManager(dna_root)
        self.objects = ObjectEngine(self.graph)
        self.resources = ResourceEngine(self.graph)
        self.execution = ExecutionEngine(self)
        self.diagnostics = DiagnosticsEngine(self)
        self.events: List[Dict[str, Any]] = []
        self.state = "created"

    def boot(self) -> Dict[str, Any]:
        self.state = "booting"
        discovered = self.dna.discover()
        self.state = "mounting"
        mount = self.dna.mount_all(self)
        self.state = "running"
        self.emit("kernel.booted", {"discovered": len(discovered), "mounted": mount.get("mounted", []), "connected": mount.get("connected", [])})
        return self.status()

    def emit(self, event_type: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        event = {"type": event_type, "payload": payload or {}}
        self.events.append(event)
        return event

    def status(self) -> Dict[str, Any]:
        return {
            "state": self.state,
            "dna": self.dna.status(),
            "graph": self.graph.status(),
            "execution": self.execution.status(),
            "events": len(self.events),
            "engines": [
                "object",
                "runtime_manager",
                "lifecycle",
                "runtime_graph",
                "discovery",
                "scheduler",
                "planner",
                "execution",
                "swarm",
                "memory",
                "knowledge",
                "communication",
                "resource",
                "security",
                "storage",
                "diagnostics",
                "evolution",
            ],
        }

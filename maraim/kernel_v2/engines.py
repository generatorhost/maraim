from typing import Any, Dict, List, Optional

from .dna_manager import DNAManager
from .event_bus import EventBusEngine
from .memory_engine import MemoryEngine
from .planner import PlannerEngine
from .scheduler import SchedulerEngine
from .execution import ExecutionEngine
from .evolution import EvolutionEngine
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
        self.event_bus = EventBusEngine()
        self.graph = RuntimeGraph()
        self.dna = DNAManager(dna_root)
        self.objects = ObjectEngine(self.graph)
        self.resources = ResourceEngine(self.graph)
        self.memory = MemoryEngine(self)
        self.planner = PlannerEngine(self)
        self.evolution = EvolutionEngine(self)
        self.scheduler = SchedulerEngine(self)
        self.execution = ExecutionEngine(self)
        self.diagnostics = DiagnosticsEngine(self)
        self.events: List[Dict[str, Any]] = []
        self.state = "created"
        self._wire_default_event_handlers()

    def _wire_default_event_handlers(self) -> None:
        self.event_bus.subscribe("execution.task_completed", lambda event: self.memory.remember("working", {"type": "event", "data": event}))
        self.event_bus.subscribe("scheduler.plan_scheduled", lambda event: self.memory.remember("collective", {"type": "event", "data": event}))
        self.event_bus.subscribe("evolution.lesson_created", lambda event: self.memory.remember("semantic", {"type": "event", "data": event}))

    def boot(self) -> Dict[str, Any]:
        self.state = "booting"
        discovered = self.dna.discover()
        self.state = "mounting"
        mount = self.dna.mount_all(self)
        self.state = "running"
        self.emit("kernel.booted", {"discovered": len(discovered), "mounted": mount.get("mounted", []), "connected": mount.get("connected", [])})
        return self.status()

    def emit(self, event_type: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        event = self.event_bus.emit(event_type, payload or {})
        self.events.append(event)
        return event

    def status(self) -> Dict[str, Any]:
        return {
            "state": self.state,
            "dna": self.dna.status(),
            "graph": self.graph.status(),
            "event_bus": self.event_bus.status(),
            "memory": self.memory.status(),
            "planner": self.planner.status(),
            "scheduler": self.scheduler.status(),
            "execution": self.execution.status(),
            "evolution": self.evolution.status(),
            "events": len(self.events),
            "engines": [
                "object",
                "runtime_manager",
                "lifecycle",
                "runtime_graph",
                "discovery",
                "event_bus",
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

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


class PlannerEngine:
    """Builds an executable task graph from RuntimeGraph relations."""

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
        self.plans: List[Dict[str, Any]] = []

    def plan(self, object_id: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = payload or {}
        obj = self.kernel.graph.get(object_id)
        if obj is None:
            return {"ok": False, "error": "runtime_not_found", "object_id": object_id}

        tasks = [{
            "id": f"task:root:{object_id}",
            "object_id": object_id,
            "relation": "root",
            "depends_on": [],
            "payload": payload,
            "priority": 0,
        }]

        for index, edge in enumerate(self.kernel.graph.outgoing(object_id), start=1):
            if edge.relation not in self.EXECUTABLE_RELATIONS:
                continue
            tasks.append({
                "id": f"task:{index}:{edge.target}",
                "object_id": edge.target,
                "relation": edge.relation,
                "depends_on": [tasks[0]["id"]],
                "payload": {"parent": object_id, "relation": edge.relation, "payload": payload},
                "priority": index,
            })

        plan = {
            "ok": True,
            "root": object_id,
            "task_count": len(tasks),
            "tasks": tasks,
        }
        self.plans.append(plan)
        self.kernel.emit("planner.plan_created", {"object_id": object_id, "tasks": len(tasks)})
        return plan

    def status(self) -> Dict[str, Any]:
        return {"plans": len(self.plans), "last": self.plans[-1] if self.plans else None}


class ExecutionEngine:
    """Task-graph execution foundation.

    Executes a PlannerEngine task graph without the Kernel knowing concrete
    runtime kinds such as Mission, Agent, Model, or Swarm.
    """

    def __init__(self, kernel: "KernelV2"):
        self.kernel = kernel
        self.runs: List[Dict[str, Any]] = []

    def execute(self, object_id: str, payload: Optional[Dict[str, Any]] = None, depth: int = 1) -> Dict[str, Any]:
        plan = self.kernel.planner.plan(object_id, payload)
        if not plan.get("ok"):
            return plan
        return self.execute_plan(plan)

    def execute_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        completed: Dict[str, Dict[str, Any]] = {}
        failed: List[Dict[str, Any]] = []

        for task in sorted(plan.get("tasks", []), key=lambda item: item.get("priority", 0)):
            missing = [dep for dep in task.get("depends_on", []) if dep not in completed]
            if missing:
                failure = {"ok": False, "task": task, "error": "missing_dependencies", "missing": missing}
                failed.append(failure)
                continue

            obj = self.kernel.graph.get(task["object_id"])
            if obj is None:
                failure = {"ok": False, "task": task, "error": "runtime_not_found"}
                failed.append(failure)
                continue

            result = {
                "ok": True,
                "task": task,
                "object": obj.status(),
                "result": obj.execute(task.get("payload", {})),
            }
            completed[task["id"]] = result

        run = {
            "ok": len(failed) == 0,
            "plan": plan,
            "completed": list(completed.values()),
            "failed": failed,
            "completed_count": len(completed),
            "failed_count": len(failed),
        }
        self.runs.append(run)
        self.kernel.emit("execution.completed", {"root": plan.get("root"), "completed": len(completed), "failed": len(failed)})
        return run

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
        self.planner = PlannerEngine(self)
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
            "planner": self.planner.status(),
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

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
            "status": "queued",
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
                "status": "queued",
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


class SchedulerEngine:
    """Schedules task graphs and supports run-next/run-all execution."""

    def __init__(self, kernel: "KernelV2"):
        self.kernel = kernel
        self.queue: List[Dict[str, Any]] = []
        self.completed: Dict[str, Dict[str, Any]] = {}
        self.failed: List[Dict[str, Any]] = []

    def schedule_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        if not plan.get("ok"):
            return plan
        scheduled = []
        for task in sorted(plan.get("tasks", []), key=lambda item: item.get("priority", 0)):
            queued_task = dict(task)
            queued_task["status"] = "queued"
            self.queue.append(queued_task)
            scheduled.append(queued_task["id"])
        self.kernel.emit("scheduler.plan_scheduled", {"root": plan.get("root"), "tasks": len(scheduled)})
        return {"ok": True, "scheduled": scheduled, "queued": len(self.queue)}

    def runnable_tasks(self) -> List[Dict[str, Any]]:
        return [
            task for task in self.queue
            if all(dep in self.completed for dep in task.get("depends_on", []))
        ]

    def run_next(self) -> Dict[str, Any]:
        runnable = self.runnable_tasks()
        if not runnable:
            return {"ok": False, "error": "queue_empty_or_blocked", "status": self.status()}
        task = sorted(runnable, key=lambda item: item.get("priority", 0))[0]
        self.queue.remove(task)
        result = self.kernel.execution.execute_task(task)
        if result.get("ok"):
            self.completed[task["id"]] = result
        else:
            self.failed.append(result)
        return {"ok": True, "task_id": task["id"], "result": result, "status": self.status()}

    def run_all(self, limit: int = 1000) -> Dict[str, Any]:
        results = []
        for _ in range(limit):
            if not self.queue:
                break
            r = self.run_next()
            if not r.get("ok"):
                break
            results.append(r)
        return {"ok": True, "processed": len(results), "results": results, "status": self.status()}

    def status(self) -> Dict[str, Any]:
        return {
            "queued": len(self.queue),
            "completed": len(self.completed),
            "failed": len(self.failed),
        }


class ExecutionEngine:
    """Task execution foundation.

    Executes Scheduler/Planner tasks without the Kernel knowing concrete runtime
    kinds such as Mission, Agent, Model, or Swarm.
    """

    def __init__(self, kernel: "KernelV2"):
        self.kernel = kernel
        self.runs: List[Dict[str, Any]] = []

    def execute(self, object_id: str, payload: Optional[Dict[str, Any]] = None, depth: int = 1) -> Dict[str, Any]:
        plan = self.kernel.planner.plan(object_id, payload)
        if not plan.get("ok"):
            return plan
        self.kernel.scheduler.schedule_plan(plan)
        return self.kernel.scheduler.run_all()

    def execute_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        self.kernel.scheduler.schedule_plan(plan)
        return self.kernel.scheduler.run_all()

    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        obj = self.kernel.graph.get(task["object_id"])
        if obj is None:
            result = {"ok": False, "task": task, "error": "runtime_not_found"}
            self.runs.append(result)
            return result
        result = {
            "ok": True,
            "task": task,
            "object": obj.status(),
            "result": obj.execute(task.get("payload", {})),
        }
        self.runs.append(result)
        self.kernel.emit("execution.task_completed", {"task_id": task.get("id"), "object_id": task.get("object_id")})
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
        self.planner = PlannerEngine(self)
        self.scheduler = SchedulerEngine(self)
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
            "scheduler": self.scheduler.status(),
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

import time
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


class MemoryEngine:
    """In-kernel memory foundation for runtime experience.

    This is intentionally in-memory only for v2 foundation. Storage-backed
    memory can be mounted later as a DNA RuntimeObject or Storage Engine layer.
    """

    def __init__(self, kernel: "KernelV2"):
        self.kernel = kernel
        self.working: List[Dict[str, Any]] = []
        self.long: List[Dict[str, Any]] = []
        self.semantic: List[Dict[str, Any]] = []
        self.procedural: List[Dict[str, Any]] = []
        self.episodic: List[Dict[str, Any]] = []
        self.collective: List[Dict[str, Any]] = []
        self.dna: List[Dict[str, Any]] = []

    def remember(self, space: str, item: Dict[str, Any]) -> Dict[str, Any]:
        target = getattr(self, space, None)
        if target is None or not isinstance(target, list):
            return {"ok": False, "error": "memory_space_not_found", "space": space}
        record = dict(item)
        record.setdefault("timestamp", time.time())
        record.setdefault("space", space)
        target.append(record)
        self.kernel.emit("memory.recorded", {"space": space, "count": len(target)})
        return {"ok": True, "space": space, "record": record}

    def recall(self, space: str, limit: int = 10) -> Dict[str, Any]:
        target = getattr(self, space, None)
        if target is None or not isinstance(target, list):
            return {"ok": False, "error": "memory_space_not_found", "space": space}
        return {"ok": True, "space": space, "items": target[-limit:]}

    def remember_experience(self, experience: Dict[str, Any], lesson: Dict[str, Any]) -> Dict[str, Any]:
        self.remember("episodic", {"type": "experience", "data": experience})
        self.remember("procedural", {"type": "lesson", "data": lesson})
        if lesson.get("recommendation"):
            self.remember("dna", {"type": "evolution_recommendation", "data": lesson})
        return {"ok": True, "experience_id": experience.get("id"), "lesson_id": lesson.get("id")}

    def status(self) -> Dict[str, Any]:
        return {
            "working": len(self.working),
            "long": len(self.long),
            "semantic": len(self.semantic),
            "procedural": len(self.procedural),
            "episodic": len(self.episodic),
            "collective": len(self.collective),
            "dna": len(self.dna),
        }


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
        started = time.time()
        for _ in range(limit):
            if not self.queue:
                break
            r = self.run_next()
            if not r.get("ok"):
                break
            results.append(r)
        run = {"ok": True, "processed": len(results), "results": results, "status": self.status(), "duration_ms": int((time.time() - started) * 1000)}
        self.kernel.evolution.observe_run(run)
        return run

    def status(self) -> Dict[str, Any]:
        return {
            "queued": len(self.queue),
            "completed": len(self.completed),
            "failed": len(self.failed),
        }


class EvolutionEngine:
    """Records execution experience and produces optimization lessons.

    This foundation does not mutate DNA yet. It creates the telemetry and
    lessons layer that future DNA evolution will consume.
    """

    def __init__(self, kernel: "KernelV2"):
        self.kernel = kernel
        self.experiences: List[Dict[str, Any]] = []
        self.lessons: List[Dict[str, Any]] = []

    def observe_run(self, run: Dict[str, Any]) -> Dict[str, Any]:
        experience = {
            "id": f"experience:{len(self.experiences) + 1}",
            "timestamp": time.time(),
            "processed": run.get("processed", 0),
            "queued": run.get("status", {}).get("queued", 0),
            "completed": run.get("status", {}).get("completed", 0),
            "failed": run.get("status", {}).get("failed", 0),
            "duration_ms": run.get("duration_ms", 0),
            "success": run.get("status", {}).get("failed", 0) == 0,
            "relations": [item.get("result", {}).get("task", {}).get("relation") for item in run.get("results", [])],
        }
        self.experiences.append(experience)
        lesson = self._lesson_from_experience(experience)
        self.lessons.append(lesson)
        self.kernel.memory.remember_experience(experience, lesson)
        self.kernel.emit("evolution.experience_recorded", {"experience_id": experience["id"], "success": experience["success"]})
        return {"ok": True, "experience": experience, "lesson": lesson}

    def _lesson_from_experience(self, experience: Dict[str, Any]) -> Dict[str, Any]:
        if experience["success"]:
            recommendation = "reuse_current_task_graph"
        else:
            recommendation = "inspect_failed_runtime_objects"
        return {
            "id": f"lesson:{len(self.lessons) + 1}",
            "experience_id": experience["id"],
            "recommendation": recommendation,
            "reason": {
                "processed": experience["processed"],
                "failed": experience["failed"],
                "duration_ms": experience["duration_ms"],
            },
        }

    def status(self) -> Dict[str, Any]:
        return {
            "experiences": len(self.experiences),
            "lessons": len(self.lessons),
            "last_experience": self.experiences[-1] if self.experiences else None,
            "last_lesson": self.lessons[-1] if self.lessons else None,
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
        started = time.time()
        obj = self.kernel.graph.get(task["object_id"])
        if obj is None:
            result = {"ok": False, "task": task, "error": "runtime_not_found", "duration_ms": int((time.time() - started) * 1000)}
            self.runs.append(result)
            return result
        result = {
            "ok": True,
            "task": task,
            "object": obj.status(),
            "result": obj.execute(task.get("payload", {})),
            "duration_ms": int((time.time() - started) * 1000),
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
        self.memory = MemoryEngine(self)
        self.planner = PlannerEngine(self)
        self.evolution = EvolutionEngine(self)
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

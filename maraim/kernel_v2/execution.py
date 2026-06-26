import time
from typing import Any, Dict, List, Optional


class ExecutionEngine:
    def __init__(self, kernel: Any):
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
            self.kernel.emit("execution.task_failed", {"task_id": task.get("id"), "object_id": task.get("object_id"), "error": "runtime_not_found"})
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

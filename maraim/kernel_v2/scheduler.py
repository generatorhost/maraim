import time
from typing import Any, Dict, List


class SchedulerEngine:
    def __init__(self, kernel: Any):
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
        return [task for task in self.queue if all(dep in self.completed for dep in task.get("depends_on", []))]

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
        self.kernel.emit("scheduler.run_completed", run)
        self.kernel.evolution.observe_run(run)
        return run

    def status(self) -> Dict[str, Any]:
        return {"queued": len(self.queue), "completed": len(self.completed), "failed": len(self.failed)}

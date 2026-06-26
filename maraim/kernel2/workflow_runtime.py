class WorkflowRuntime:
    def __init__(self, event_bus, registry, scheduler, memory):
        self.event_bus = event_bus
        self.registry = registry
        self.scheduler = scheduler
        self.memory = memory
        self.workflows = {}
        self.runs = {}

    def load_from_registry(self):
        self.workflows = {item["id"]: item["payload"] for item in self.registry.list("workflow")}
        self.event_bus.emit("workflows:loaded", {"count": len(self.workflows)})
        return {"ok": True, "count": len(self.workflows)}

    def run(self, workflow_id, payload=None):
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return {"ok": False, "error": f"workflow_not_found:{workflow_id}"}

        payload = payload or {}
        steps = workflow.get("steps") or [{"id": "plan", "type": "plan"}, {"id": "route", "type": "route"}]
        scheduled = []
        run_id = f"{workflow_id}:{len(self.runs)+1}"
        run_steps = []

        for index, step in enumerate(steps):
            step_id = step.get("id", f"step_{index+1}")
            task = {"type": step.get("type", "workflow_step"), "workflow_id": workflow_id, "run_id": run_id, "step_id": step_id, "payload": payload}
            q = self.scheduler.submit(task, priority=index + 1)
            scheduled.append(q)
            run_steps.append({"id": step_id, "type": task["type"], "status": "queued", "task_id": q.get("task_id"), "output": None})

        self.runs[run_id] = {
            "run_id": run_id,
            "workflow_id": workflow_id,
            "status": "queued",
            "progress": 0,
            "current_step": run_steps[0]["id"] if run_steps else None,
            "steps": run_steps,
            "payload": payload
        }

        self.memory.remember_working(f"workflow:{workflow_id}:last_payload", payload)
        self.event_bus.emit("workflow:scheduled", {"workflow_id": workflow_id, "run_id": run_id, "steps": len(scheduled)})
        return {"ok": True, "workflow_id": workflow_id, "run_id": run_id, "scheduled": scheduled, "state": self.runs[run_id]}

    def mark_task_completed(self, task, result):
        run_id = task.get("run_id")
        step_id = task.get("step_id")
        if not run_id or run_id not in self.runs:
            return {"ok": False, "error": "run_not_found"}

        run = self.runs[run_id]
        for step in run["steps"]:
            if step["id"] == step_id:
                step["status"] = "completed"
                step["output"] = result
                break

        total = len(run["steps"]) or 1
        done = len([x for x in run["steps"] if x["status"] == "completed"])
        run["progress"] = int((done / total) * 100)

        pending = [x for x in run["steps"] if x["status"] != "completed"]
        run["current_step"] = pending[0]["id"] if pending else None
        run["status"] = "completed" if not pending else "running"

        self.event_bus.emit("workflow:step_completed", {"run_id": run_id, "step_id": step_id, "progress": run["progress"]})
        return {"ok": True, "run": run}

    def status(self):
        return {"count": len(self.workflows), "workflows": sorted(self.workflows.keys()), "runs": self.runs}

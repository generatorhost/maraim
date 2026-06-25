class WorkflowRuntime:
    def __init__(self, event_bus, registry, scheduler, memory):
        self.event_bus = event_bus
        self.registry = registry
        self.scheduler = scheduler
        self.memory = memory
        self.workflows = {}

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
        for index, step in enumerate(steps):
            task = {"type": step.get("type", "workflow_step"), "workflow_id": workflow_id, "step_id": step.get("id", f"step_{index+1}"), "payload": payload}
            scheduled.append(self.scheduler.submit(task, priority=index + 1))
        self.memory.remember_working(f"workflow:{workflow_id}:last_payload", payload)
        self.event_bus.emit("workflow:scheduled", {"workflow_id": workflow_id, "steps": len(scheduled)})
        return {"ok": True, "workflow_id": workflow_id, "scheduled": scheduled}

    def status(self):
        return {"count": len(self.workflows), "workflows": sorted(self.workflows.keys())}

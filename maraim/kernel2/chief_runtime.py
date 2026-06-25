class ChiefRuntime:
    def __init__(self, event_bus, registry, team_runtime):
        self.event_bus = event_bus
        self.registry = registry
        self.team_runtime = team_runtime
        self.chiefs = {}
        self.state = "created"

    def load_from_registry(self):
        self.chiefs = {
            item["id"]: {"id": item["id"], "payload": item["payload"], "state": "ready", "decisions": []}
            for item in self.registry.list("chief")
        }
        self.state = "ready"
        self.event_bus.emit("chiefs:loaded", {"count": len(self.chiefs)})
        return {"ok": True, "count": len(self.chiefs)}

    def route_task(self, task):
        task_type = task.get("type", "general")
        if task_type in ["scrape", "project_discovery"]:
            target_team = "scouting"
        elif task_type in ["analyze", "project_analysis"]:
            target_team = "analysis"
        elif task_type in ["proposal", "proposal_generation"]:
            target_team = "proposal"
        else:
            target_team = task.get("team") or "scouting"
        result = self.team_runtime.assign(target_team, task)
        self.event_bus.emit("chief:routed_task", {"task": task, "target_team": target_team, "result": result})
        return {"ok": result.get("ok", False), "target_team": target_team, "result": result}

    def status(self):
        return {"state": self.state, "count": len(self.chiefs), "chiefs": [{"id": c["id"], "state": c["state"]} for c in self.chiefs.values()]}

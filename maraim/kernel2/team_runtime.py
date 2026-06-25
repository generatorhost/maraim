class TeamRuntime:
    def __init__(self, event_bus, registry, agent_runtime):
        self.event_bus = event_bus
        self.registry = registry
        self.agent_runtime = agent_runtime
        self.teams = {}

    def load_from_registry(self):
        self.teams = {
            item["id"]: {"id": item["id"], "payload": item["payload"], "state": "ready", "tasks": []}
            for item in self.registry.list("team")
        }
        self.event_bus.emit("teams:loaded", {"count": len(self.teams)})
        return {"ok": True, "count": len(self.teams)}

    def assign(self, team_id, task):
        if team_id not in self.teams:
            return {"ok": False, "error": f"team_not_found:{team_id}"}
        team = self.teams[team_id]
        team["tasks"].append(task)
        team["state"] = "working"
        agents = team["payload"].get("agents") or []
        assigned = [self.agent_runtime.assign(agent_id, task) for agent_id in agents]
        self.event_bus.emit("team:assigned", {"team_id": team_id, "task": task, "agents": assigned})
        return {"ok": True, "team_id": team_id, "assigned_agents": assigned}

    def status(self):
        return {"count": len(self.teams), "teams": [{"id": t["id"], "state": t["state"], "tasks": len(t["tasks"])} for t in self.teams.values()]}

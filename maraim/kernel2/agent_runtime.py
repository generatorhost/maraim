class AgentRuntime:
    def __init__(self, event_bus, registry, mcp_runtime):
        self.event_bus = event_bus
        self.registry = registry
        self.mcp_runtime = mcp_runtime
        self.agents = {}

    def load_from_registry(self):
        self.agents = {
            item["id"]: {"id": item["id"], "payload": item["payload"], "state": "ready", "tasks": []}
            for item in self.registry.list("agent")
        }
        self.event_bus.emit("agents:loaded", {"count": len(self.agents)})
        return {"ok": True, "count": len(self.agents)}

    def assign(self, agent_id, task):
        if agent_id not in self.agents:
            return {"ok": False, "error": f"agent_not_found:{agent_id}"}
        agent = self.agents[agent_id]
        agent["tasks"].append(task)
        agent["state"] = "working"
        self.event_bus.emit("agent:assigned", {"agent_id": agent_id, "task": task})
        return {"ok": True, "agent_id": agent_id, "task": task}

    def status(self):
        return {"count": len(self.agents), "agents": [{"id": a["id"], "state": a["state"], "tasks": len(a["tasks"])} for a in self.agents.values()]}

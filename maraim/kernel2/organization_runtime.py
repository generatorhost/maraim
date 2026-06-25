class OrganizationRuntime:
    def __init__(self, event_bus, chief_runtime, team_runtime, agent_runtime):
        self.event_bus = event_bus
        self.chief_runtime = chief_runtime
        self.team_runtime = team_runtime
        self.agent_runtime = agent_runtime
        self.state = "created"

    def start(self):
        agents = self.agent_runtime.load_from_registry()
        teams = self.team_runtime.load_from_registry()
        chiefs = self.chief_runtime.load_from_registry()
        self.state = "running"
        self.event_bus.emit("organization:started", {"agents": agents, "teams": teams, "chiefs": chiefs})
        return self.status()

    def route_task(self, task):
        return self.chief_runtime.route_task(task)

    def status(self):
        return {"state": self.state, "chief": self.chief_runtime.status(), "teams": self.team_runtime.status(), "agents": self.agent_runtime.status()}

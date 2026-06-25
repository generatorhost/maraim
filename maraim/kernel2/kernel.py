from .lifecycle import KernelState
from .service_container import ServiceContainer
from .event_bus import EventBus
from .registry import RuntimeRegistry
from .dna_runtime import DNARuntime
from .runtime_manager import RuntimeManager
from .mcp_runtime import MCPRuntime
from .agent_runtime import AgentRuntime
from .team_runtime import TeamRuntime
from .chief_runtime import ChiefRuntime
from .organization_runtime import OrganizationRuntime

class MaraimKernel:
    def __init__(self, dna_root="dna/source"):
        self.state = KernelState.CREATED
        self.container = ServiceContainer()
        self.event_bus = EventBus()
        self.registry = RuntimeRegistry()
        self.runtime_manager = RuntimeManager(self.event_bus)
        self.dna_runtime = DNARuntime(self.registry, dna_root=dna_root)
        self.mcp_runtime = MCPRuntime(self.event_bus)
        self.agent_runtime = AgentRuntime(self.event_bus, self.registry, self.mcp_runtime)
        self.team_runtime = TeamRuntime(self.event_bus, self.registry, self.agent_runtime)
        self.chief_runtime = ChiefRuntime(self.event_bus, self.registry, self.team_runtime)
        self.organization_runtime = OrganizationRuntime(self.event_bus, self.chief_runtime, self.team_runtime, self.agent_runtime)
        self.boot_log = []

    def boot(self):
        self._set_state(KernelState.BOOTING)
        self.container.register("event_bus", lambda: self.event_bus)
        self.container.register("registry", lambda: self.registry)
        self.container.register("runtime_manager", lambda: self.runtime_manager)
        self.container.register("dna_runtime", lambda: self.dna_runtime)
        self.container.register("mcp_runtime", lambda: self.mcp_runtime)
        self.container.register("agent_runtime", lambda: self.agent_runtime)
        self.container.register("team_runtime", lambda: self.team_runtime)
        self.container.register("chief_runtime", lambda: self.chief_runtime)
        self.container.register("organization_runtime", lambda: self.organization_runtime)
        self.runtime_manager.mount("dna", self.dna_runtime)
        self.runtime_manager.mount("mcp", self.mcp_runtime)
        self.runtime_manager.mount("agents", self.agent_runtime)
        self.runtime_manager.mount("teams", self.team_runtime)
        self.runtime_manager.mount("chief", self.chief_runtime)
        self.runtime_manager.mount("organization", self.organization_runtime)
        self._register_builtin_tools()
        self._set_state(KernelState.READY)
        return self.status()

    def start(self):
        if self.state == KernelState.CREATED:
            self.boot()
        self._set_state(KernelState.LOADING)
        dna_result = self.dna_runtime.load()
        self.event_bus.emit("dna:loaded", dna_result)
        self.organization_runtime.start()
        self._set_state(KernelState.RUNNING)
        return self.status()

    def shutdown(self):
        self._set_state(KernelState.STOPPING)
        self._set_state(KernelState.SHUTDOWN)

    def route_task(self, task):
        return self.organization_runtime.route_task(task)

    def status(self):
        return {
            "state": self.state.value,
            "services": self.container.list_services(),
            "runtimes": self.runtime_manager.status(),
            "registry_counts": self.registry.counts(),
            "organization": self.organization_runtime.status(),
            "mcp_tools": self.mcp_runtime.list_tools(),
        }

    def _set_state(self, state):
        self.state = state
        self.boot_log.append(state.value)
        self.event_bus.emit("kernel:state", {"state": state.value})

    def _register_builtin_tools(self):
        self.mcp_runtime.register_tool("kernel.status", lambda _: self.status(), "Return kernel status")
        self.mcp_runtime.register_tool("dna.reload", lambda _: self.dna_runtime.reload(), "Reload DNA source into registry")
        self.mcp_runtime.register_tool("chief.route_task", lambda payload: self.route_task(payload), "Route a task through Chief Runtime")

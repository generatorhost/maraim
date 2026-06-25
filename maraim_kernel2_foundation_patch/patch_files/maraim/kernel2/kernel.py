from .lifecycle import KernelState
from .service_container import ServiceContainer
from .event_bus import EventBus
from .registry import RuntimeRegistry
from .dna_runtime import DNARuntime
from .runtime_manager import RuntimeManager
from .mcp_runtime import MCPRuntime

class MaraimKernel:
    def __init__(self, dna_root="dna/source"):
        self.state = KernelState.CREATED
        self.container = ServiceContainer()
        self.event_bus = EventBus()
        self.registry = RuntimeRegistry()
        self.runtime_manager = RuntimeManager(self.event_bus)
        self.dna_runtime = DNARuntime(self.registry, dna_root=dna_root)
        self.mcp_runtime = MCPRuntime(self.event_bus)
        self.boot_log = []

    def boot(self):
        self._set_state(KernelState.BOOTING)
        self.container.register("event_bus", lambda: self.event_bus)
        self.container.register("registry", lambda: self.registry)
        self.container.register("runtime_manager", lambda: self.runtime_manager)
        self.container.register("dna_runtime", lambda: self.dna_runtime)
        self.container.register("mcp_runtime", lambda: self.mcp_runtime)
        self.runtime_manager.mount("dna", self.dna_runtime)
        self.runtime_manager.mount("mcp", self.mcp_runtime)
        self._register_builtin_tools()
        self._set_state(KernelState.READY)
        return self.status()

    def start(self):
        if self.state == KernelState.CREATED:
            self.boot()
        self._set_state(KernelState.LOADING)
        dna_result = self.dna_runtime.load()
        self.event_bus.emit("dna:loaded", dna_result)
        self._set_state(KernelState.RUNNING)
        return self.status()

    def shutdown(self):
        self._set_state(KernelState.STOPPING)
        self._set_state(KernelState.SHUTDOWN)

    def status(self):
        return {
            "state": self.state.value,
            "services": self.container.list_services(),
            "runtimes": self.runtime_manager.status(),
            "registry_counts": self.registry.counts(),
            "mcp_tools": self.mcp_runtime.list_tools(),
        }

    def _set_state(self, state):
        self.state = state
        self.boot_log.append(state.value)
        self.event_bus.emit("kernel:state", {"state": state.value})

    def _register_builtin_tools(self):
        self.mcp_runtime.register_tool("kernel.status", lambda _: self.status(), "Return kernel status")
        self.mcp_runtime.register_tool("dna.reload", lambda _: self.dna_runtime.reload(), "Reload DNA source into registry")

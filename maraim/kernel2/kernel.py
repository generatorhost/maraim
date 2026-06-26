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
from .memory_runtime import MemoryRuntime
from .scheduler_runtime import SchedulerRuntime
from .workflow_runtime import WorkflowRuntime
from .task_executor_runtime import TaskExecutorRuntime

class MaraimKernel:
    def __init__(self, dna_root="dna/source", scraping_runner=None):
        self.state = KernelState.CREATED
        self.container = ServiceContainer()
        self.event_bus = EventBus()
        self.registry = RuntimeRegistry()
        self.runtime_manager = RuntimeManager(self.event_bus)
        self.dna_runtime = DNARuntime(self.registry, dna_root=dna_root)
        self.mcp_runtime = MCPRuntime(self.event_bus)
        self.memory_runtime = MemoryRuntime(self.event_bus)
        self.scheduler_runtime = SchedulerRuntime(self.event_bus)
        self.workflow_runtime = WorkflowRuntime(self.event_bus, self.registry, self.scheduler_runtime, self.memory_runtime)
        self.agent_runtime = AgentRuntime(self.event_bus, self.registry, self.mcp_runtime)
        self.team_runtime = TeamRuntime(self.event_bus, self.registry, self.agent_runtime)
        self.chief_runtime = ChiefRuntime(self.event_bus, self.registry, self.team_runtime)
        self.organization_runtime = OrganizationRuntime(self.event_bus, self.chief_runtime, self.team_runtime, self.agent_runtime)
        self.task_executor_runtime = TaskExecutorRuntime(self.event_bus, self.memory_runtime, self.organization_runtime, scraping_runner=scraping_runner)
        self.boot_log = []

    def boot(self):
        self._set_state(KernelState.BOOTING)
        services = {
            "event_bus": self.event_bus, "registry": self.registry, "runtime_manager": self.runtime_manager,
            "dna_runtime": self.dna_runtime, "mcp_runtime": self.mcp_runtime, "memory_runtime": self.memory_runtime,
            "scheduler_runtime": self.scheduler_runtime, "workflow_runtime": self.workflow_runtime,
            "agent_runtime": self.agent_runtime, "team_runtime": self.team_runtime, "chief_runtime": self.chief_runtime,
            "organization_runtime": self.organization_runtime,
            "task_executor_runtime": self.task_executor_runtime,
        }
        for name, service in services.items():
            self.container.register(name, lambda service=service: service)

        self.runtime_manager.mount("dna", self.dna_runtime)
        self.runtime_manager.mount("mcp", self.mcp_runtime)
        self.runtime_manager.mount("memory", self.memory_runtime)
        self.runtime_manager.mount("scheduler", self.scheduler_runtime)
        self.runtime_manager.mount("workflow", self.workflow_runtime)
        self.runtime_manager.mount("agents", self.agent_runtime)
        self.runtime_manager.mount("teams", self.team_runtime)
        self.runtime_manager.mount("chief", self.chief_runtime)
        self.runtime_manager.mount("organization", self.organization_runtime)
        self.runtime_manager.mount("task_executor", self.task_executor_runtime)

        self._register_builtin_tools()
        self._set_state(KernelState.READY)
        return self.status()

    def start(self):
        if self.state == KernelState.CREATED:
            self.boot()
        self._set_state(KernelState.LOADING)
        dna_result = self.dna_runtime.load()
        self.event_bus.emit("dna:loaded", dna_result)
        self.workflow_runtime.load_from_registry()
        self.organization_runtime.start()
        self._set_state(KernelState.RUNNING)
        return self.status()

    def shutdown(self):
        self._set_state(KernelState.STOPPING)
        self._set_state(KernelState.SHUTDOWN)

    def route_task(self, task):
        scheduled = self.scheduler_runtime.submit(task, priority=task.get("priority", 5))
        routed = self.organization_runtime.route_task(task)
        self.memory_runtime.remember_long({"task": task, "routed": routed})
        return {"ok": routed.get("ok", False), "scheduled": scheduled, "routed": routed}

    def run_workflow(self, workflow_id, payload=None):
        return self.workflow_runtime.run(workflow_id, payload or {})

    def run_next_task(self):
        item = self.scheduler_runtime.next()
        if not item:
            return {"ok": False, "error": "queue_empty"}
        task = item["task"]
        executed = self.task_executor_runtime.execute(task)
        self.scheduler_runtime.complete(item["id"], executed)
        return {"ok": True, "task_id": item["id"], "task": task, "executed": executed}

    def status(self):
        return {
            "state": self.state.value,
            "services": self.container.list_services(),
            "runtimes": self.runtime_manager.status(),
            "registry_counts": self.registry.counts(),
            "organization": self.organization_runtime.status(),
            "workflow": self.workflow_runtime.status(),
            "scheduler": self.scheduler_runtime.status(),
            "memory": self.memory_runtime.status(),
            "task_executor": self.task_executor_runtime.status(),
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
        self.mcp_runtime.register_tool("workflow.run", lambda payload: self.run_workflow(payload.get("workflow_id", "project-acquisition"), payload), "Run workflow through Scheduler")
        self.mcp_runtime.register_tool("memory.status", lambda _: self.memory_runtime.status(), "Return memory status")
        self.mcp_runtime.register_tool("scheduler.status", lambda _: self.scheduler_runtime.status(), "Return scheduler status")
        self.mcp_runtime.register_tool("scheduler.run_next", lambda _: self.run_next_task(), "Run next queued task")

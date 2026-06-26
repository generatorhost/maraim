from maraim.kernel_v2.runtime_types import AgentRuntime


class SampleAgentRuntime(AgentRuntime):
    def __init__(self):
        super().__init__(
            namespace="agents.sample",
            key="research_agent",
            version="1.0.0",
            capabilities=["research", "task_execution"],
            metadata={"role": "sample_research_agent"},
        )

    def execute(self, payload=None):
        return {
            "ok": True,
            "agent": self.id,
            "result": "Sample research agent executed.",
            "payload": payload or {},
        }

from maraim.kernel_v2.runtime_types import SwarmRuntime


class SampleSwarmRuntime(SwarmRuntime):
    def __init__(self):
        super().__init__(
            namespace="swarms.sample",
            key="research_swarm",
            version="1.0.0",
            capabilities=["swarm_spawn", "parallel_execution"],
            metadata={"description": "Sample swarm proving any RuntimeObject can be swarm-capable."},
        )

    def execute(self, payload=None):
        payload = payload or {}
        count = int(payload.get("count", 3))
        return self.spawn(count=count, payload=payload)

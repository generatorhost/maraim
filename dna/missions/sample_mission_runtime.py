from maraim.kernel_v2.runtime_types import MissionRuntime


class SampleMissionRuntime(MissionRuntime):
    def __init__(self):
        super().__init__(
            namespace="missions.sample",
            key="research_mission",
            version="1.0.0",
            capabilities=["mission_planning", "task_graph"],
            metadata={"description": "Sample mission proving missions are RuntimeObjects."},
        )

    def execute(self, payload=None):
        payload = payload or {}
        return {
            "ok": True,
            "mission": self.id,
            "plan": ["discover", "analyze", "write", "validate"],
            "payload": payload,
        }

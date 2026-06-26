from typing import Any, Dict, Optional

from .runtime_object import DNARuntime


class CommanderRuntime(DNARuntime):
    def __init__(self, namespace="commanders", key="commander", version="1.0.0", **kwargs):
        super().__init__(namespace=namespace, key=key, version=version, kind="commander", **kwargs)


class MissionRuntime(DNARuntime):
    def __init__(self, namespace="missions", key="mission", version="1.0.0", **kwargs):
        super().__init__(namespace=namespace, key=key, version=version, kind="mission", **kwargs)


class SwarmRuntime(DNARuntime):
    def __init__(self, namespace="swarms", key="swarm", version="1.0.0", **kwargs):
        super().__init__(namespace=namespace, key=key, version=version, kind="swarm", **kwargs)

    def spawn(self, count: int = 1, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return {"ok": True, "swarm": self.id, "spawned": max(0, count), "payload": payload or {}}


class TeamRuntime(DNARuntime):
    def __init__(self, namespace="teams", key="team", version="1.0.0", **kwargs):
        super().__init__(namespace=namespace, key=key, version=version, kind="team", **kwargs)


class AgentRuntime(DNARuntime):
    def __init__(self, namespace="agents", key="agent", version="1.0.0", **kwargs):
        super().__init__(namespace=namespace, key=key, version=version, kind="agent", **kwargs)


class SkillRuntime(DNARuntime):
    def __init__(self, namespace="skills", key="skill", version="1.0.0", **kwargs):
        super().__init__(namespace=namespace, key=key, version=version, kind="skill", **kwargs)


class CapabilityRuntime(DNARuntime):
    def __init__(self, namespace="capabilities", key="capability", version="1.0.0", **kwargs):
        super().__init__(namespace=namespace, key=key, version=version, kind="capability", **kwargs)


class ToolRuntime(DNARuntime):
    def __init__(self, namespace="tools", key="tool", version="1.0.0", **kwargs):
        super().__init__(namespace=namespace, key=key, version=version, kind="tool", **kwargs)


class PluginRuntime(DNARuntime):
    def __init__(self, namespace="plugins", key="plugin", version="1.0.0", **kwargs):
        super().__init__(namespace=namespace, key=key, version=version, kind="plugin", **kwargs)


class ModelRuntime(DNARuntime):
    def __init__(self, namespace="models", key="model", version="1.0.0", **kwargs):
        super().__init__(namespace=namespace, key=key, version=version, kind="model", **kwargs)


class ArtifactRuntime(DNARuntime):
    def __init__(self, namespace="artifacts", key="artifact", version="1.0.0", **kwargs):
        super().__init__(namespace=namespace, key=key, version=version, kind="artifact", **kwargs)

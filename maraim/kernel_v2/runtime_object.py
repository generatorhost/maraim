from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Iterable, List, Optional


class RuntimeState(str, Enum):
    CREATED = "created"
    DISCOVERED = "discovered"
    VALIDATED = "validated"
    MOUNTED = "mounted"
    CONNECTED = "connected"
    OBSERVING = "observing"
    SCALING = "scaling"
    RETIRED = "retired"
    ERROR = "error"


@dataclass(frozen=True)
class RuntimeIdentity:
    namespace: str
    key: str
    version: str = "1.0.0"

    @property
    def id(self) -> str:
        return f"{self.namespace}.{self.key}@{self.version}"


@dataclass
class RuntimeObject:
    """Universal Maraim v2 object.

    The Kernel only understands RuntimeObject. Agent, Team, Mission, Plugin,
    Model, GGUF, ONNX, Tool, Dashboard, Connector, or any future entity are
    specializations in DNA space, not hard-coded Kernel types.
    """

    namespace: str
    key: str
    version: str = "1.0.0"
    kind: str = "runtime"
    capabilities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    state: RuntimeState = RuntimeState.CREATED

    @property
    def identity(self) -> RuntimeIdentity:
        return RuntimeIdentity(self.namespace, self.key, self.version)

    @property
    def id(self) -> str:
        return self.identity.id

    def discover(self, kernel: Any) -> "RuntimeObject":
        self.state = RuntimeState.DISCOVERED
        return self

    def validate(self, kernel: Any) -> "RuntimeObject":
        self.state = RuntimeState.VALIDATED
        return self

    def mount(self, kernel: Any) -> "RuntimeObject":
        self.state = RuntimeState.MOUNTED
        return self

    def connect(self, kernel: Any) -> "RuntimeObject":
        self.state = RuntimeState.CONNECTED
        return self

    def observe(self, kernel: Any) -> Dict[str, Any]:
        self.state = RuntimeState.OBSERVING
        return self.status()

    def scale(self, kernel: Any, target: Optional[Any] = None) -> "RuntimeObject":
        self.state = RuntimeState.SCALING
        return self

    def retire(self, kernel: Any) -> "RuntimeObject":
        self.state = RuntimeState.RETIRED
        return self

    def execute(self, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return {"ok": True, "runtime": self.id, "payload": payload or {}}

    def status(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "namespace": self.namespace,
            "key": self.key,
            "version": self.version,
            "kind": self.kind,
            "state": self.state.value,
            "capabilities": list(self.capabilities),
            "metadata": dict(self.metadata),
        }

    def provides(self, capability: str) -> bool:
        return capability in self.capabilities


class DNARuntime(RuntimeObject):
    """Alias base for DNA-hosted RuntimeObjects.

    This class intentionally adds no new Kernel contract. It exists for
    developer readability while preserving the rule: Kernel knows only
    RuntimeObject.
    """

    pass

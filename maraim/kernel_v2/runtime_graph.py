from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .runtime_object import RuntimeObject


@dataclass
class RuntimeEdge:
    source: str
    relation: str
    target: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class RuntimeGraph:
    """Dynamic graph of RuntimeObjects.

    The graph is the primary structure of Maraim v2. It replaces hard-coded
    lists such as agents[], plugins[], tools[], or models[].
    """

    def __init__(self):
        self.nodes: Dict[str, RuntimeObject] = {}
        self.edges: List[RuntimeEdge] = []

    def add_node(self, obj: RuntimeObject) -> RuntimeObject:
        if obj.id in self.nodes:
            raise ValueError(f"duplicate_runtime_object:{obj.id}")
        self.nodes[obj.id] = obj
        return obj

    def remove_node(self, object_id: str) -> bool:
        if object_id not in self.nodes:
            return False
        del self.nodes[object_id]
        self.edges = [e for e in self.edges if e.source != object_id and e.target != object_id]
        return True

    def connect(self, source: RuntimeObject | str, relation: str, target: RuntimeObject | str, **metadata: Any) -> RuntimeEdge:
        source_id = source.id if isinstance(source, RuntimeObject) else source
        target_id = target.id if isinstance(target, RuntimeObject) else target
        if source_id not in self.nodes:
            raise KeyError(f"source_not_found:{source_id}")
        if target_id not in self.nodes:
            raise KeyError(f"target_not_found:{target_id}")
        edge = RuntimeEdge(source_id, relation, target_id, dict(metadata))
        self.edges.append(edge)
        return edge

    def get(self, object_id: str) -> Optional[RuntimeObject]:
        return self.nodes.get(object_id)

    def find_by_capability(self, capability: str) -> List[RuntimeObject]:
        return [obj for obj in self.nodes.values() if obj.provides(capability)]

    def outgoing(self, object_id: str, relation: Optional[str] = None) -> List[RuntimeEdge]:
        return [e for e in self.edges if e.source == object_id and (relation is None or e.relation == relation)]

    def incoming(self, object_id: str, relation: Optional[str] = None) -> List[RuntimeEdge]:
        return [e for e in self.edges if e.target == object_id and (relation is None or e.relation == relation)]

    def status(self) -> Dict[str, Any]:
        return {
            "nodes": len(self.nodes),
            "edges": len(self.edges),
            "objects": [obj.status() for obj in self.nodes.values()],
            "relations": [edge.__dict__ for edge in self.edges],
        }

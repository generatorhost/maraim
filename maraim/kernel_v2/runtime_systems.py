from typing import Any, Dict, Iterable, List, Optional, Set

from .runtime_object import RuntimeObject


class RuntimeSystemEngine:
    """Base registry for DNA-hosted runtime systems.

    This is not a new Kernel contract. It is a thin operating layer that
    registers extracted RuntimeObjects and records their relationships in
    RuntimeGraph so plugins, connectors, providers, and tools can be mounted,
    resolved, bound, invoked, and observed lazily.
    """

    runtime_kind = "runtime"
    capability_name = "runtime_system"
    binding_relation = "binds_runtime"

    def __init__(self, kernel: Any):
        self.kernel = kernel
        self.registry: Dict[str, RuntimeObject] = {}
        self.bindings: List[Dict[str, Any]] = []
        self.invocations: List[Dict[str, Any]] = []

    def accepts(self, spec: Dict[str, Any]) -> bool:
        return spec.get("kind") == self.runtime_kind

    def register_from_runtime_objects(self, runtime_objects: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
        registered: List[str] = []
        reused: List[str] = []
        skipped: List[str] = []
        for spec in runtime_objects:
            if not self.accepts(spec):
                skipped.append(spec.get("id", "unknown"))
                continue
            obj = self._object_from_spec(spec)
            existing = self.kernel.graph.get(obj.id)
            if existing is None:
                self.kernel.graph.add_node(obj)
                registered.append(obj.id)
            else:
                obj = existing
                reused.append(obj.id)
            self.registry[obj.id] = obj
        self._emit("registered", {"registered": registered, "reused": reused, "skipped": len(skipped)})
        return {"ok": True, "kind": self.runtime_kind, "registered": registered, "reused": reused, "skipped": len(skipped), "count": len(registered) + len(reused)}

    def resolve(self, capability: Optional[str] = None, source_path: Optional[str] = None) -> Dict[str, Any]:
        candidates = list(self.registry.values())
        if capability:
            candidates = [obj for obj in candidates if obj.provides(capability)]
        if source_path:
            candidates = [obj for obj in candidates if obj.metadata.get("source_path") == source_path]
        return {"ok": True, "kind": self.runtime_kind, "count": len(candidates), "runtimes": [obj.status() for obj in candidates]}

    def bind(self, source_id: str, target_id: str, relation: Optional[str] = None, **metadata: Any) -> Dict[str, Any]:
        source = self.kernel.graph.get(source_id)
        target = self.kernel.graph.get(target_id)
        if source is None:
            return {"ok": False, "error": "source_not_found", "source": source_id}
        if target is None:
            return {"ok": False, "error": "target_not_found", "target": target_id}
        rel = relation or self.binding_relation
        if not self._edge_exists(source.id, rel, target.id):
            edge = self.kernel.graph.connect(source, rel, target, **metadata)
            record = edge.__dict__
        else:
            record = {"source": source.id, "relation": rel, "target": target.id, "metadata": dict(metadata), "reused": True}
        self.bindings.append(record)
        self._emit("bound", record)
        return {"ok": True, "binding": record}

    def invoke(self, runtime_id: str, action: str = "default", payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        runtime = self.registry.get(runtime_id) or self.kernel.graph.get(runtime_id)
        if runtime is None:
            return {"ok": False, "error": "runtime_not_found", "runtime": runtime_id}
        result = runtime.execute({"action": action, "payload": payload or {}, "system": self.runtime_kind})
        invocation = {"runtime": runtime.id, "action": action, "payload": payload or {}, "result": result}
        self.invocations.append(invocation)
        self._emit("invoked", invocation)
        return {"ok": True, "invocation": invocation}

    def status(self) -> Dict[str, Any]:
        capability_index: Dict[str, int] = {}
        for obj in self.registry.values():
            for capability in obj.capabilities:
                capability_index[capability] = capability_index.get(capability, 0) + 1
        return {
            "kind": self.runtime_kind,
            "runtimes": len(self.registry),
            "bindings": len(self.bindings),
            "invocations": len(self.invocations),
            "capabilities": capability_index,
        }

    def _object_from_spec(self, spec: Dict[str, Any]) -> RuntimeObject:
        namespace, key, version = self._parse_id(spec.get("id", ""))
        capabilities: Set[str] = set(spec.get("capabilities", []))
        capabilities.add(self.capability_name)
        metadata = dict(spec.get("metadata", {}))
        metadata["source_path"] = spec.get("source_path")
        metadata["dna_runtime_system"] = self.runtime_kind
        return RuntimeObject(
            namespace=namespace,
            key=key,
            version=version,
            kind=spec.get("kind", self.runtime_kind),
            capabilities=sorted(capabilities),
            metadata=metadata,
        )

    def _parse_id(self, value: str) -> tuple[str, str, str]:
        version = "1.0.0"
        raw = value or f"runtime.{self.runtime_kind}.unnamed@{version}"
        if "@" in raw:
            raw, version = raw.rsplit("@", 1)
        if "." in raw:
            namespace, key = raw.rsplit(".", 1)
        else:
            namespace, key = self.runtime_kind, raw
        return namespace, key, version

    def _edge_exists(self, source: str, relation: str, target: str) -> bool:
        return any(edge.source == source and edge.relation == relation and edge.target == target for edge in self.kernel.graph.edges)

    def _emit(self, suffix: str, payload: Dict[str, Any]) -> None:
        if hasattr(self.kernel, "emit"):
            self.kernel.emit(f"{self.runtime_kind}_runtime.{suffix}", payload)


class PluginRuntimeEngine(RuntimeSystemEngine):
    runtime_kind = "plugin"
    capability_name = "plugin_runtime"
    binding_relation = "plugin_binds_runtime"

    def accepts(self, spec: Dict[str, Any]) -> bool:
        return spec.get("kind") == "plugin"


class ConnectorRuntimeEngine(RuntimeSystemEngine):
    runtime_kind = "connector"
    capability_name = "connector_runtime"
    binding_relation = "connector_binds_runtime"

    def accepts(self, spec: Dict[str, Any]) -> bool:
        return spec.get("kind") in {"connector", "integration"}


class ProviderEngine(RuntimeSystemEngine):
    runtime_kind = "provider"
    capability_name = "provider_runtime"
    binding_relation = "provider_binds_runtime"

    def accepts(self, spec: Dict[str, Any]) -> bool:
        return spec.get("kind") == "provider"


class ToolRuntimeEngine(RuntimeSystemEngine):
    runtime_kind = "tool"
    capability_name = "tool_runtime"
    binding_relation = "tool_binds_runtime"

    def accepts(self, spec: Dict[str, Any]) -> bool:
        return spec.get("kind") == "tool"

from typing import Any, Dict, Iterable, List, Optional, Set

from .runtime_store import RuntimeStore


class DependencyResolverV2:
    """Dependency resolver foundation for RuntimeGraph and RuntimeStore.

    The resolver is graph-first and in-memory only. It can derive dependency
    edges from extracted package graphs, register them, inspect missing runtime
    references, detect cycles, and produce a deterministic install/mount order.
    """

    DEPENDENCY_RELATIONS = {
        "depends_on",
        "requires",
        "uses_configuration",
        "can_use_model",
        "can_use_tool",
        "can_use_connector",
        "can_use_storage",
        "can_call_service",
        "governed_by",
        "plugin_uses_connector",
        "connector_uses_provider",
        "tool_uses_provider",
    }

    def __init__(self, kernel: Any = None, store: Optional[RuntimeStore] = None):
        self.kernel = kernel
        self.store = store or RuntimeStore(kernel)
        self.edges: List[Dict[str, Any]] = []
        self.runs: List[Dict[str, Any]] = []

    def register_edges(self, edges: Iterable[Dict[str, Any]], relations: Optional[Set[str]] = None) -> Dict[str, Any]:
        allowed = relations or self.DEPENDENCY_RELATIONS
        added: List[Dict[str, Any]] = []
        for edge in edges:
            relation = edge.get("relation")
            source = edge.get("source")
            target = edge.get("target")
            if not source or not target or relation not in allowed:
                continue
            normalized = {"source": source, "relation": relation, "target": target, "metadata": dict(edge.get("metadata", {}))}
            if not self._edge_exists(normalized):
                self.edges.append(normalized)
                added.append(normalized)
        return {"ok": True, "added": added, "count": len(added), "total": len(self.edges)}

    def register_from_package(self, package: Dict[str, Any]) -> Dict[str, Any]:
        specs = package.get("runtime_objects", [])
        graph_edges = package.get("graph_edges", [])
        stored = self.store.register_from_specs(specs, source="dependency_resolver")
        registered = self.register_edges(graph_edges)
        return {"ok": True, "stored": stored, "edges": registered}

    def resolve(self, root_id: Optional[str] = None) -> Dict[str, Any]:
        graph = self._build_graph()
        nodes = self._nodes(root_id, graph) if root_id else self._all_nodes(graph)
        missing = self._missing(nodes)
        cycles = self._cycles(graph, nodes)
        order = self._topological_order(graph, nodes)
        result = {"ok": not cycles, "root": root_id, "order": order, "missing": sorted(missing), "cycles": cycles, "nodes": len(nodes), "edges": len(self.edges)}
        self.runs.append(result)
        if self.kernel is not None and hasattr(self.kernel, "emit"):
            self.kernel.emit("dependency_resolver_v2.resolved", result)
        return result

    def explain(self, runtime_id: str) -> Dict[str, Any]:
        incoming = [edge for edge in self.edges if edge["target"] == runtime_id]
        outgoing = [edge for edge in self.edges if edge["source"] == runtime_id]
        exists = self.store.get(runtime_id).get("ok", False)
        return {"ok": True, "runtime": runtime_id, "exists": exists, "incoming": incoming, "outgoing": outgoing}

    def status(self) -> Dict[str, Any]:
        return {"edges": len(self.edges), "runs": len(self.runs), "last": self.runs[-1] if self.runs else None}

    def _edge_exists(self, edge: Dict[str, Any]) -> bool:
        return any(item["source"] == edge["source"] and item["relation"] == edge["relation"] and item["target"] == edge["target"] for item in self.edges)

    def _build_graph(self) -> Dict[str, Set[str]]:
        graph: Dict[str, Set[str]] = {}
        for edge in self.edges:
            graph.setdefault(edge["source"], set()).add(edge["target"])
            graph.setdefault(edge["target"], set())
        return graph

    def _all_nodes(self, graph: Dict[str, Set[str]]) -> Set[str]:
        nodes = set(graph)
        nodes.update(self.store.records.keys())
        return nodes

    def _nodes(self, root_id: str, graph: Dict[str, Set[str]]) -> Set[str]:
        seen: Set[str] = set()
        stack = [root_id]
        while stack:
            node = stack.pop()
            if node in seen:
                continue
            seen.add(node)
            stack.extend(sorted(graph.get(node, set()) - seen))
        return seen

    def _missing(self, nodes: Set[str]) -> Set[str]:
        return {node for node in nodes if not self.store.get(node).get("ok", False)}

    def _cycles(self, graph: Dict[str, Set[str]], nodes: Set[str]) -> List[List[str]]:
        cycles: List[List[str]] = []
        visiting: Set[str] = set()
        visited: Set[str] = set()
        path: List[str] = []

        def visit(node: str) -> None:
            if node in visiting:
                if node in path:
                    cycles.append(path[path.index(node):] + [node])
                return
            if node in visited:
                return
            visiting.add(node)
            path.append(node)
            for target in sorted(graph.get(node, set())):
                if target in nodes:
                    visit(target)
            path.pop()
            visiting.remove(node)
            visited.add(node)

        for node in sorted(nodes):
            visit(node)
        return cycles

    def _topological_order(self, graph: Dict[str, Set[str]], nodes: Set[str]) -> List[str]:
        visited: Set[str] = set()
        order: List[str] = []

        def visit(node: str) -> None:
            if node in visited:
                return
            visited.add(node)
            for target in sorted(graph.get(node, set())):
                if target in nodes:
                    visit(target)
            order.append(node)

        for node in sorted(nodes):
            visit(node)
        return order

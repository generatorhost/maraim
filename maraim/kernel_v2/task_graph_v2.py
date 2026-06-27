import time
from typing import Any, Dict, Iterable, List, Optional, Set

from .dependency_resolver_v2 import DependencyResolverV2


class TaskGraphV2:
    """Task graph foundation built on runtime dependency resolution.

    This layer creates deterministic task plans without executing work. It maps
    runtime dependency order into task nodes, validates dependency readiness, and
    exposes ready/blocked task views for later Scheduler and Execution adapters.
    """

    def __init__(self, kernel: Any = None, resolver: Optional[DependencyResolverV2] = None):
        self.kernel = kernel
        self.resolver = resolver or DependencyResolverV2(kernel)
        self.graphs: Dict[str, Dict[str, Any]] = {}
        self.history: List[Dict[str, Any]] = []

    def build_from_runtime(self, root_id: str, goal: str = "runtime_plan") -> Dict[str, Any]:
        resolved = self.resolver.resolve(root_id)
        tasks: List[Dict[str, Any]] = []
        for index, runtime_id in enumerate(resolved.get("order", [])):
            task_id = f"task.{index + 1}.{self._safe(runtime_id)}"
            upstream = [edge["target"] for edge in self.resolver.edges if edge["source"] == runtime_id]
            tasks.append({
                "id": task_id,
                "runtime": runtime_id,
                "goal": goal,
                "status": "blocked" if runtime_id in resolved.get("missing", []) else "pending",
                "depends_on_runtimes": sorted(set(upstream)),
                "metadata": {"order": index + 1},
            })
        graph_id = f"task_graph:{self._safe(root_id)}:{len(self.graphs) + 1}"
        graph = {
            "ok": resolved.get("ok", False),
            "id": graph_id,
            "root": root_id,
            "goal": goal,
            "tasks": tasks,
            "missing": resolved.get("missing", []),
            "cycles": resolved.get("cycles", []),
            "created_at": time.time(),
        }
        self.graphs[graph_id] = graph
        self._log("built", graph_id, {"root": root_id, "tasks": len(tasks)})
        return graph

    def ready_tasks(self, graph_id: str, completed_runtimes: Optional[Iterable[str]] = None) -> Dict[str, Any]:
        graph = self.graphs.get(graph_id)
        if graph is None:
            return {"ok": False, "error": "task_graph_not_found", "graph": graph_id}
        completed = set(completed_runtimes or [])
        missing = set(graph.get("missing", []))
        ready = []
        blocked = []
        for task in graph.get("tasks", []):
            deps = set(task.get("depends_on_runtimes", []))
            if task["runtime"] in missing or not deps.issubset(completed | {task["runtime"]}):
                blocked.append(task)
            else:
                ready.append(task)
        return {"ok": True, "graph": graph_id, "ready": ready, "blocked": blocked, "ready_count": len(ready), "blocked_count": len(blocked)}

    def mark_task(self, graph_id: str, task_id: str, status: str) -> Dict[str, Any]:
        graph = self.graphs.get(graph_id)
        if graph is None:
            return {"ok": False, "error": "task_graph_not_found", "graph": graph_id}
        for task in graph.get("tasks", []):
            if task["id"] == task_id:
                task["status"] = status
                self._log("task_marked", graph_id, {"task": task_id, "status": status})
                return {"ok": True, "task": task}
        return {"ok": False, "error": "task_not_found", "task": task_id}

    def export_plan(self, graph_id: str) -> Dict[str, Any]:
        graph = self.graphs.get(graph_id)
        if graph is None:
            return {"ok": False, "error": "task_graph_not_found", "graph": graph_id}
        return {
            "ok": True,
            "graph": graph_id,
            "task_count": len(graph.get("tasks", [])),
            "steps": [
                {
                    "task": task["id"],
                    "runtime": task["runtime"],
                    "status": task["status"],
                    "depends_on": task.get("depends_on_runtimes", []),
                }
                for task in graph.get("tasks", [])
            ],
        }

    def status(self) -> Dict[str, Any]:
        return {"graphs": len(self.graphs), "history": len(self.history), "last": self.history[-1] if self.history else None}

    def _safe(self, value: str) -> str:
        return "".join(ch if ch.isalnum() else "_" for ch in value)[:80].strip("_") or "runtime"

    def _log(self, action: str, graph_id: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        item = {"action": action, "graph": graph_id, "metadata": metadata or {}, "created_at": time.time()}
        self.history.append(item)
        if self.kernel is not None and hasattr(self.kernel, "emit"):
            self.kernel.emit(f"task_graph_v2.{action}", item)

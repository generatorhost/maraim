import time
from typing import Any, Dict, Iterable, List, Optional, Set

from .permission_sandbox import PermissionSandbox
from .task_graph_v2 import TaskGraphV2


class ExecutionAdapterV2:
    """Safe execution adapter foundation for TaskGraph v2.

    This adapter does not run user code, spawn subprocesses, access networks, or
    mutate external systems. It records deterministic simulated execution results
    for task graph steps so later real executors can attach to the same contract.
    Every run can be gated by PermissionSandbox before simulated execution.
    """

    default_permissions = ["execute_simulated"]

    def __init__(self, kernel: Any = None, task_graph: Optional[TaskGraphV2] = None, sandbox: Optional[PermissionSandbox] = None):
        self.kernel = kernel
        self.task_graph = task_graph or TaskGraphV2(kernel)
        self.sandbox = sandbox or PermissionSandbox(kernel)
        self.runs: Dict[str, Dict[str, Any]] = {}
        self.history: List[Dict[str, Any]] = []

    def dry_run(self, graph_id: str) -> Dict[str, Any]:
        plan = self.task_graph.export_plan(graph_id)
        if not plan.get("ok"):
            return plan
        steps = [{"task": step["task"], "runtime": step["runtime"], "would_execute": step["status"] != "blocked"} for step in plan.get("steps", [])]
        return {"ok": True, "graph": graph_id, "steps": steps, "count": len(steps)}

    def run(
        self,
        graph_id: str,
        completed_runtimes: Optional[Iterable[str]] = None,
        mode: str = "simulated",
        permissions: Optional[Iterable[str]] = None,
        require_permissions: bool = True,
    ) -> Dict[str, Any]:
        plan = self.task_graph.export_plan(graph_id)
        if not plan.get("ok"):
            return plan
        run_id = f"run:{graph_id}:{len(self.runs) + 1}"
        completed: Set[str] = set(completed_runtimes or [])
        required_permissions = list(permissions or self.default_permissions)
        results: List[Dict[str, Any]] = []
        failed = []

        for step in plan.get("steps", []):
            permission_plan = self.sandbox.build_plan(step["runtime"], required_permissions, mode=mode) if require_permissions else {"ok": True, "can_execute": True, "missing": []}
            deps = set(step.get("depends_on", []))
            ready = deps.issubset(completed | {step["runtime"]}) and step["status"] != "blocked" and permission_plan["can_execute"]
            status = "completed" if ready else "blocked"
            result = {
                "task": step["task"],
                "runtime": step["runtime"],
                "mode": mode,
                "status": status,
                "ready": ready,
                "permissions": permission_plan,
                "created_at": time.time(),
            }
            results.append(result)
            if ready:
                completed.add(step["runtime"])
                self.task_graph.mark_task(graph_id, step["task"], "completed")
            else:
                failed.append(result)

        run_record = {
            "ok": not failed,
            "id": run_id,
            "graph": graph_id,
            "mode": mode,
            "results": results,
            "blocked": failed,
            "completed_runtimes": sorted(completed),
            "required_permissions": required_permissions,
            "created_at": time.time(),
        }
        self.runs[run_id] = run_record
        self._log("run", run_id, {"graph": graph_id, "ok": run_record["ok"]})
        return run_record

    def resume(self, run_id: str) -> Dict[str, Any]:
        previous = self.runs.get(run_id)
        if previous is None:
            return {"ok": False, "error": "run_not_found", "run": run_id}
        return self.run(
            previous["graph"],
            completed_runtimes=previous.get("completed_runtimes", []),
            mode=previous.get("mode", "simulated"),
            permissions=previous.get("required_permissions", self.default_permissions),
        )

    def status(self) -> Dict[str, Any]:
        return {"runs": len(self.runs), "history": len(self.history), "last": self.history[-1] if self.history else None}

    def _log(self, action: str, run_id: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        item = {"action": action, "run": run_id, "metadata": metadata or {}, "created_at": time.time()}
        self.history.append(item)
        if self.kernel is not None and hasattr(self.kernel, "emit"):
            self.kernel.emit(f"execution_adapter_v2.{action}", item)

import time
from typing import Any, Dict, Iterable, List


FOUNDATION_COMPONENTS = [
    "kernel_core",
    "runtime_objects",
    "runtime_graph",
    "dna_extraction",
    "dna_package_engine",
    "model_runtime_foundation",
    "runtime_systems",
    "runtime_store",
    "hot_reload",
    "mount_manager",
    "storage_health",
    "source_adapters_foundation",
    "dependency_resolver_v2",
    "task_graph_v2",
    "execution_adapter_v2",
    "result_artifacts",
    "permission_sandbox",
    "audit_trail",
    "metrics_engine",
    "trace_engine",
    "report_builder",
    "snapshot_builder",
    "phase3_contracts",
    "phase4_contracts",
    "real_adapters_foundation",
    "sandbox_enforcement_foundation",
    "sqlite_audit_adapter",
    "audit_persistence_bridge",
    "persistence_health",
    "persistence_checkpoint",
    "persistence_recovery",
]


class FoundationCompletionLedger:
    """Completion ledger for Kernel v2 foundation components."""

    def __init__(self, kernel: Any = None):
        self.kernel = kernel
        self.components: Dict[str, Dict[str, Any]] = {}

    def initialize(self, completed: Iterable[str] = ()) -> Dict[str, Any]:
        completed_set = set(completed)
        for name in FOUNDATION_COMPONENTS:
            self.components[name] = {
                "name": name,
                "status": "completed" if name in completed_set else "planned",
                "created_at": time.time(),
            }
        return self.summary()

    def mark(self, name: str, status: str = "completed") -> Dict[str, Any]:
        if name not in self.components:
            return {"ok": False, "error": "component_not_found", "component": name}
        self.components[name]["status"] = status
        self.components[name]["updated_at"] = time.time()
        if self.kernel is not None and hasattr(self.kernel, "emit"):
            self.kernel.emit("foundation_completion.marked", self.components[name])
        return {"ok": True, "component": self.components[name]}

    def summary(self) -> Dict[str, Any]:
        total = len(self.components)
        completed = len([item for item in self.components.values() if item["status"] == "completed"])
        percent = round((completed / total) * 100, 2) if total else 0
        return {"ok": True, "total": total, "completed": completed, "planned": total - completed, "percent": percent}

    def report(self) -> Dict[str, Any]:
        return {"ok": True, "summary": self.summary(), "components": list(self.components.values())}

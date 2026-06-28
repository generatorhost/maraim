import time
from typing import Any, Dict, Iterable, List


GIT_ADAPTER_PLAN_STEPS = [
    "repo_url_validation",
    "target_path_policy",
    "branch_ref_policy",
    "credential_policy",
    "network_permission_gate",
    "filesystem_permission_gate",
    "workspace_allocation",
    "preflight_audit_event",
    "preflight_metrics_event",
    "preflight_trace_event",
    "dry_run_manifest",
    "clone_command_shape",
    "pull_command_shape",
    "checkout_command_shape",
    "result_artifact_shape",
    "rollback_workspace_plan",
    "failure_classification",
    "post_run_audit_event",
    "post_run_health_check",
    "promotion_acceptance_gate",
]


class GitAdapterImplementationPlan:
    """Twenty-step implementation plan for the real Git adapter."""

    def __init__(self, kernel: Any = None):
        self.kernel = kernel
        self.records: Dict[str, Dict[str, Any]] = {}

    def initialize(self) -> Dict[str, Any]:
        for step in GIT_ADAPTER_PLAN_STEPS:
            self.records[step] = {"step": step, "status": "planned", "created_at": time.time()}
        return self.summary()

    def attach_outputs(self, outputs: Dict[str, Iterable[str]]) -> Dict[str, Any]:
        missing = []
        for step in GIT_ADAPTER_PLAN_STEPS:
            values = list(outputs.get(step, []))
            if not values:
                missing.append(step)
            elif step in self.records:
                self.records[step]["outputs"] = values
        return {"ok": not missing, "missing": missing, "summary": self.summary()}

    def mark(self, step: str, status: str) -> Dict[str, Any]:
        if step not in self.records:
            return {"ok": False, "error": "step_not_found", "step": step}
        self.records[step]["status"] = status
        self.records[step]["updated_at"] = time.time()
        if self.kernel is not None and hasattr(self.kernel, "emit"):
            self.kernel.emit("git_adapter_plan.marked", self.records[step])
        return {"ok": True, "record": self.records[step]}

    def summary(self) -> Dict[str, Any]:
        total = len(GIT_ADAPTER_PLAN_STEPS)
        initialized = len(self.records)
        with_outputs = len([item for item in self.records.values() if item.get("outputs")])
        return {"ok": initialized == total, "total": total, "initialized": initialized, "with_outputs": with_outputs}

    def report(self) -> Dict[str, Any]:
        return {"ok": True, "summary": self.summary(), "steps": list(self.records.values())}

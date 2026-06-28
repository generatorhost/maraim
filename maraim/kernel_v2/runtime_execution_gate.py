import time
from typing import Any, Dict, Iterable, List


class RuntimeExecutionGate:
    """Pre-execution gate for real engine runs.

    This gate does not execute commands. It verifies that a planned run has an
    existing workspace and that every requested operation is allowed by a
    sandbox enforcement layer.
    """

    def __init__(self, workspace_manager: Any, sandbox: Any, kernel: Any = None):
        self.workspace_manager = workspace_manager
        self.sandbox = sandbox
        self.kernel = kernel
        self.decisions: List[Dict[str, Any]] = []

    def evaluate(self, workspace_id: str, sandbox_profile: str, operations: Iterable[str], engine: str = "runtime") -> Dict[str, Any]:
        workspace_status = self.workspace_manager.status()
        workspace_exists = any(item.get("id") == workspace_id for item in workspace_status.get("items", []))
        if not workspace_exists:
            decision = self._decision(False, "workspace_not_found", workspace_id, sandbox_profile, list(operations), engine, {})
            return {"ok": True, "allowed": False, "decision": decision}
        enforcement = self.sandbox.require_all(sandbox_profile, operations)
        allowed = bool(enforcement.get("ok"))
        reason = "allowed" if allowed else "sandbox_blocked"
        decision = self._decision(allowed, reason, workspace_id, sandbox_profile, list(operations), engine, enforcement)
        return {"ok": True, "allowed": allowed, "decision": decision}

    def bind_if_allowed(self, workspace_id: str, sandbox_profile: str, operations: Iterable[str], engine: str, resource: str) -> Dict[str, Any]:
        evaluation = self.evaluate(workspace_id, sandbox_profile, operations, engine)
        if not evaluation["allowed"]:
            return {"ok": True, "bound": False, "evaluation": evaluation}
        binding = self.workspace_manager.bind(workspace_id, engine, resource)
        return {"ok": True, "bound": binding.get("ok", False), "evaluation": evaluation, "binding": binding}

    def status(self) -> Dict[str, Any]:
        allowed = len([item for item in self.decisions if item["allowed"]])
        blocked = len(self.decisions) - allowed
        return {"ok": True, "decisions": len(self.decisions), "allowed": allowed, "blocked": blocked}

    def _decision(self, allowed: bool, reason: str, workspace_id: str, sandbox_profile: str, operations: List[str], engine: str, details: Dict[str, Any]) -> Dict[str, Any]:
        decision = {
            "allowed": allowed,
            "reason": reason,
            "workspace_id": workspace_id,
            "sandbox_profile": sandbox_profile,
            "operations": operations,
            "engine": engine,
            "details": details,
            "created_at": time.time(),
        }
        self.decisions.append(decision)
        if self.kernel is not None and hasattr(self.kernel, "emit"):
            self.kernel.emit("runtime_execution_gate.decision", decision)
        return decision

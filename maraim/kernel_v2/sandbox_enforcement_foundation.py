import time
from typing import Any, Dict, Iterable, List, Optional


class SandboxEnforcementFoundation:
    """Foundation enforcement layer for runtime safety decisions.

    This does not create an OS sandbox. It centralizes deny-by-default decisions
    for operations before real adapters or real execution are allowed to run.
    """

    sensitive_operations = {"network", "subprocess", "filesystem_write", "database_write", "real_clone", "archive_extract", "folder_scan"}

    def __init__(self, kernel: Any = None):
        self.kernel = kernel
        self.profiles: Dict[str, Dict[str, Any]] = {}
        self.decisions: List[Dict[str, Any]] = []

    def define_profile(self, profile_id: str, allowed: Iterable[str], denied: Optional[Iterable[str]] = None, mode: str = "foundation") -> Dict[str, Any]:
        allowed_set = sorted(set(item.strip().lower() for item in allowed if item))
        denied_set = sorted(set(item.strip().lower() for item in (denied or []) if item))
        profile = {"id": profile_id, "allowed": allowed_set, "denied": denied_set, "mode": mode, "created_at": time.time()}
        self.profiles[profile_id] = profile
        self._emit("profile_defined", profile)
        return {"ok": True, "profile": profile}

    def decide(self, profile_id: str, operation: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        operation = operation.strip().lower()
        profile = self.profiles.get(profile_id)
        if profile is None:
            return self._decision(profile_id, operation, False, "profile_not_found", metadata)
        if operation in profile["denied"]:
            return self._decision(profile_id, operation, False, "explicitly_denied", metadata)
        if operation not in profile["allowed"]:
            return self._decision(profile_id, operation, False, "not_allowed", metadata)
        if operation in self.sensitive_operations and profile.get("mode") != "production_enforced":
            return self._decision(profile_id, operation, False, "sensitive_operation_requires_production_enforcement", metadata)
        return self._decision(profile_id, operation, True, "allowed", metadata)

    def require_all(self, profile_id: str, operations: Iterable[str]) -> Dict[str, Any]:
        decisions = [self.decide(profile_id, operation) for operation in operations]
        blocked = [item for item in decisions if not item["allowed"]]
        return {"ok": not blocked, "profile": profile_id, "decisions": decisions, "blocked": blocked}

    def attach_to_plan(self, plan: Dict[str, Any], profile_id: str) -> Dict[str, Any]:
        operations = plan.get("operations", [])
        enforcement = self.require_all(profile_id, operations)
        secured = dict(plan)
        secured["sandbox_profile"] = profile_id
        secured["sandbox_enforcement"] = enforcement
        secured["can_execute"] = bool(plan.get("can_execute")) and enforcement["ok"]
        return {"ok": True, "plan": secured}

    def status(self) -> Dict[str, Any]:
        allowed = len([item for item in self.decisions if item["allowed"]])
        blocked = len(self.decisions) - allowed
        return {"profiles": len(self.profiles), "decisions": len(self.decisions), "allowed": allowed, "blocked": blocked}

    def _decision(self, profile_id: str, operation: str, allowed: bool, reason: str, metadata: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        decision = {"profile": profile_id, "operation": operation, "allowed": allowed, "reason": reason, "metadata": metadata or {}, "created_at": time.time()}
        self.decisions.append(decision)
        self._emit("decision", decision)
        return decision

    def _emit(self, suffix: str, payload: Dict[str, Any]) -> None:
        if self.kernel is not None and hasattr(self.kernel, "emit"):
            self.kernel.emit(f"sandbox_enforcement_foundation.{suffix}", payload)

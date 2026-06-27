import time
from typing import Any, Dict, Iterable, List, Optional, Set


class PermissionSandbox:
    """Policy-only sandbox foundation for Kernel v2.

    This layer does not enforce an operating-system sandbox. It defines a small
    in-memory permission contract so real executors and real adapters can later
    require explicit grants before doing sensitive work.
    """

    def __init__(self, kernel: Any = None):
        self.kernel = kernel
        self.grants: Dict[str, Set[str]] = {}
        self.denials: Dict[str, Set[str]] = {}
        self.decisions: List[Dict[str, Any]] = []

    def grant(self, runtime_id: str, permissions: Iterable[str], reason: str = "grant") -> Dict[str, Any]:
        values = {self._normalize(item) for item in permissions if item}
        self.grants.setdefault(runtime_id, set()).update(values)
        self._emit("grant", {"runtime": runtime_id, "permissions": sorted(values), "reason": reason})
        return {"ok": True, "runtime": runtime_id, "granted": sorted(self.grants[runtime_id])}

    def deny(self, runtime_id: str, permissions: Iterable[str], reason: str = "deny") -> Dict[str, Any]:
        values = {self._normalize(item) for item in permissions if item}
        self.denials.setdefault(runtime_id, set()).update(values)
        self._emit("deny", {"runtime": runtime_id, "permissions": sorted(values), "reason": reason})
        return {"ok": True, "runtime": runtime_id, "denied": sorted(self.denials[runtime_id])}

    def evaluate(self, runtime_id: str, permission: str) -> Dict[str, Any]:
        item = self._normalize(permission)
        denied = item in self.denials.get(runtime_id, set()) or item in self.denials.get("*", set())
        granted = item in self.grants.get(runtime_id, set()) or item in self.grants.get("*", set())
        decision = {
            "ok": True,
            "runtime": runtime_id,
            "permission": item,
            "allowed": granted and not denied,
            "granted": granted,
            "denied": denied,
            "created_at": time.time(),
        }
        self.decisions.append(decision)
        self._emit("evaluate", decision)
        return decision

    def require(self, runtime_id: str, permissions: Iterable[str]) -> Dict[str, Any]:
        decisions = [self.evaluate(runtime_id, permission) for permission in permissions]
        allowed = all(item["allowed"] for item in decisions)
        return {"ok": allowed, "runtime": runtime_id, "decisions": decisions, "missing": [item["permission"] for item in decisions if not item["allowed"]]}

    def build_plan(self, runtime_id: str, requested_permissions: Iterable[str], mode: str = "foundation") -> Dict[str, Any]:
        required = self.require(runtime_id, requested_permissions)
        return {
            "ok": required["ok"],
            "runtime": runtime_id,
            "mode": mode,
            "requested_permissions": list(requested_permissions),
            "missing": required["missing"],
            "can_execute": required["ok"],
            "plan": "policy_only_no_os_sandbox",
            "created_at": time.time(),
        }

    def status(self) -> Dict[str, Any]:
        return {
            "grant_subjects": len(self.grants),
            "deny_subjects": len(self.denials),
            "decisions": len(self.decisions),
            "last": self.decisions[-1] if self.decisions else None,
        }

    def _normalize(self, permission: str) -> str:
        return permission.strip().lower().replace(" ", "_")

    def _emit(self, suffix: str, payload: Dict[str, Any]) -> None:
        if self.kernel is not None and hasattr(self.kernel, "emit"):
            self.kernel.emit(f"permission_sandbox.{suffix}", payload)

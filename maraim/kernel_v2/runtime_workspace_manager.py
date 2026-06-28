import time
from pathlib import PurePosixPath
from typing import Any, Dict, List


class RuntimeWorkspaceManager:
    """Safe in-memory workspace registry for future real engine execution.

    This manager does not create, delete, or modify filesystem paths. It only
    validates logical workspace names and records planned workspace bindings.
    """

    def __init__(self, root: str = "runtime-workspaces", kernel: Any = None):
        self.root = root.strip("/") or "runtime-workspaces"
        self.kernel = kernel
        self.workspaces: Dict[str, Dict[str, Any]] = {}
        self.bindings: List[Dict[str, Any]] = []

    def create_workspace(self, workspace_id: str, purpose: str = "runtime") -> Dict[str, Any]:
        validation = self._validate_id(workspace_id)
        if not validation["ok"]:
            return validation
        if workspace_id in self.workspaces:
            return {"ok": False, "error": "workspace_exists", "workspace_id": workspace_id}
        logical_path = str(PurePosixPath(self.root) / workspace_id)
        workspace = {
            "id": workspace_id,
            "purpose": purpose,
            "logical_path": logical_path,
            "status": "planned",
            "created_at": time.time(),
        }
        self.workspaces[workspace_id] = workspace
        self._emit("created", workspace)
        return {"ok": True, "workspace": workspace}

    def bind(self, workspace_id: str, engine: str, resource: str) -> Dict[str, Any]:
        if workspace_id not in self.workspaces:
            return {"ok": False, "error": "workspace_not_found", "workspace_id": workspace_id}
        if not engine or not resource:
            return {"ok": False, "error": "engine_and_resource_required"}
        binding = {
            "workspace_id": workspace_id,
            "engine": engine,
            "resource": resource,
            "created_at": time.time(),
        }
        self.bindings.append(binding)
        self._emit("bound", binding)
        return {"ok": True, "binding": binding}

    def mark(self, workspace_id: str, status: str) -> Dict[str, Any]:
        if workspace_id not in self.workspaces:
            return {"ok": False, "error": "workspace_not_found", "workspace_id": workspace_id}
        self.workspaces[workspace_id]["status"] = status
        self.workspaces[workspace_id]["updated_at"] = time.time()
        return {"ok": True, "workspace": self.workspaces[workspace_id]}

    def status(self) -> Dict[str, Any]:
        return {
            "ok": True,
            "root": self.root,
            "workspaces": len(self.workspaces),
            "bindings": len(self.bindings),
            "items": list(self.workspaces.values()),
        }

    def _validate_id(self, value: str) -> Dict[str, Any]:
        if not value or value.strip() != value:
            return {"ok": False, "error": "invalid_workspace_id", "workspace_id": value}
        if "/" in value or "\\" in value or ".." in value:
            return {"ok": False, "error": "unsafe_workspace_id", "workspace_id": value}
        return {"ok": True}

    def _emit(self, suffix: str, payload: Dict[str, Any]) -> None:
        if self.kernel is not None and hasattr(self.kernel, "emit"):
            self.kernel.emit(f"runtime_workspace_manager.{suffix}", payload)

import time
from typing import Any, Dict, List, Optional

from .storage_engine import RuntimeStorageEngine


class ResultArtifactV2:
    """Result artifact foundation for simulated execution outputs.

    Stores execution results in RuntimeStorageEngine using an in-memory namespace.
    It does not write files, call external services, or persist to a database.
    """

    namespace = "execution_results"

    def __init__(self, kernel: Any = None, storage: Optional[RuntimeStorageEngine] = None):
        self.kernel = kernel
        self.storage = storage or RuntimeStorageEngine(kernel)
        self.artifacts: List[Dict[str, Any]] = []

    def capture_run(self, run_result: Dict[str, Any], label: str = "execution_run") -> Dict[str, Any]:
        if not run_result.get("id"):
            return {"ok": False, "error": "run_id_missing"}
        artifact_id = self._artifact_id(run_result["id"], label)
        permission_summary = self._permission_summary(run_result)
        artifact = {
            "id": artifact_id,
            "label": label,
            "run": run_result["id"],
            "graph": run_result.get("graph"),
            "ok": run_result.get("ok", False),
            "mode": run_result.get("mode"),
            "required_permissions": run_result.get("required_permissions", []),
            "permission_summary": permission_summary,
            "results": run_result.get("results", []),
            "blocked": run_result.get("blocked", []),
            "completed_runtimes": run_result.get("completed_runtimes", []),
            "created_at": time.time(),
        }
        stored = self.storage.put(self.namespace, artifact_id, artifact, metadata={"label": label, "run": run_result["id"]})
        self.artifacts.append(artifact)
        self._emit("captured", {"artifact": artifact_id, "run": run_result["id"], "permissions": permission_summary})
        return {"ok": stored.get("ok", False), "artifact": artifact, "stored": stored}

    def get(self, artifact_id: str) -> Dict[str, Any]:
        return self.storage.get(self.namespace, artifact_id)

    def list(self) -> Dict[str, Any]:
        return self.storage.list(self.namespace)

    def summarize(self, artifact_id: str) -> Dict[str, Any]:
        item = self.get(artifact_id)
        if not item.get("ok"):
            return item
        artifact = item["record"]["value"]
        return {
            "ok": True,
            "artifact": artifact_id,
            "run": artifact.get("run"),
            "graph": artifact.get("graph"),
            "result_count": len(artifact.get("results", [])),
            "blocked_count": len(artifact.get("blocked", [])),
            "completed_count": len(artifact.get("completed_runtimes", [])),
            "permission_summary": artifact.get("permission_summary", {}),
            "successful": artifact.get("ok", False),
        }

    def status(self) -> Dict[str, Any]:
        return {"artifacts": len(self.artifacts), "storage": self.storage.status()}

    def _permission_summary(self, run_result: Dict[str, Any]) -> Dict[str, Any]:
        allowed = 0
        blocked = 0
        missing: Dict[str, int] = {}
        for item in run_result.get("results", []):
            permissions = item.get("permissions", {})
            if permissions.get("can_execute"):
                allowed += 1
            else:
                blocked += 1
            for permission in permissions.get("missing", []):
                missing[permission] = missing.get(permission, 0) + 1
        return {"allowed": allowed, "blocked": blocked, "missing": missing}

    def _artifact_id(self, run_id: str, label: str) -> str:
        safe_run = "".join(ch if ch.isalnum() else "_" for ch in run_id)[:80].strip("_")
        safe_label = "".join(ch if ch.isalnum() else "_" for ch in label)[:40].strip("_") or "artifact"
        return f"{safe_label}.{safe_run}.{len(self.artifacts) + 1}"

    def _emit(self, suffix: str, payload: Dict[str, Any]) -> None:
        if self.kernel is not None and hasattr(self.kernel, "emit"):
            self.kernel.emit(f"result_artifact_v2.{suffix}", payload)

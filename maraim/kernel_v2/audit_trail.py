import time
from typing import Any, Dict, Iterable, List, Optional


class RuntimeAuditTrail:
    """In-memory audit trail foundation for Kernel v2.

    This records structured runtime events without filesystem writes, database
    writes, external services, or network calls. Later persistence adapters can
    consume the same event shape.
    """

    def __init__(self, kernel: Any = None):
        self.kernel = kernel
        self.events: List[Dict[str, Any]] = []

    def record(self, event_type: str, subject: str, action: str, status: str = "ok", metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        event = {
            "id": f"audit:{len(self.events) + 1}",
            "type": event_type,
            "subject": subject,
            "action": action,
            "status": status,
            "metadata": dict(metadata or {}),
            "created_at": time.time(),
        }
        self.events.append(event)
        if self.kernel is not None and hasattr(self.kernel, "emit"):
            self.kernel.emit("runtime_audit.recorded", event)
        return {"ok": True, "event": event}

    def record_many(self, events: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
        recorded = [self.record(item.get("type", "runtime"), item.get("subject", "unknown"), item.get("action", "unknown"), item.get("status", "ok"), item.get("metadata", {}))["event"] for item in events]
        return {"ok": True, "events": recorded, "count": len(recorded)}

    def query(self, event_type: Optional[str] = None, subject: Optional[str] = None, action: Optional[str] = None, status: Optional[str] = None) -> Dict[str, Any]:
        items = list(self.events)
        if event_type is not None:
            items = [item for item in items if item["type"] == event_type]
        if subject is not None:
            items = [item for item in items if item["subject"] == subject]
        if action is not None:
            items = [item for item in items if item["action"] == action]
        if status is not None:
            items = [item for item in items if item["status"] == status]
        return {"ok": True, "count": len(items), "events": items}

    def capture_run(self, run_result: Dict[str, Any]) -> Dict[str, Any]:
        run_id = run_result.get("id", "unknown_run")
        events = [{"type": "execution", "subject": run_id, "action": "run", "status": "ok" if run_result.get("ok") else "blocked", "metadata": {"graph": run_result.get("graph"), "mode": run_result.get("mode")}}]
        for result in run_result.get("results", []):
            events.append({
                "type": "execution_task",
                "subject": result.get("runtime", "unknown_runtime"),
                "action": result.get("task", "task"),
                "status": result.get("status", "unknown"),
                "metadata": {"ready": result.get("ready"), "permissions": result.get("permissions", {})},
            })
        return self.record_many(events)

    def capture_artifact(self, artifact_result: Dict[str, Any]) -> Dict[str, Any]:
        artifact = artifact_result.get("artifact", {})
        return self.record(
            "artifact",
            artifact.get("id", "unknown_artifact"),
            "capture",
            "ok" if artifact_result.get("ok") else "failed",
            {"run": artifact.get("run"), "permission_summary": artifact.get("permission_summary", {})},
        )

    def status(self) -> Dict[str, Any]:
        by_type: Dict[str, int] = {}
        by_status: Dict[str, int] = {}
        for event in self.events:
            by_type[event["type"]] = by_type.get(event["type"], 0) + 1
            by_status[event["status"]] = by_status.get(event["status"], 0) + 1
        return {"events": len(self.events), "by_type": by_type, "by_status": by_status, "last": self.events[-1] if self.events else None}

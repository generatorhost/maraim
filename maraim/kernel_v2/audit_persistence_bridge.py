from typing import Any, Dict, List, Optional

from .audit_trail import RuntimeAuditTrail
from .sqlite_audit_adapter import SQLiteAuditAdapter


class AuditPersistenceBridge:
    """Bridge RuntimeAuditTrail events into an audit persistence adapter."""

    def __init__(self, audit: RuntimeAuditTrail, adapter: SQLiteAuditAdapter, kernel: Any = None):
        self.audit = audit
        self.adapter = adapter
        self.kernel = kernel
        self.last_flushed_index = 0
        self.flushes: List[Dict[str, Any]] = []

    def flush_new(self) -> Dict[str, Any]:
        events = self.audit.events[self.last_flushed_index :]
        if not events:
            return self._flush_result([], "no_new_events")
        recorded = self.adapter.record_many(events)
        self.last_flushed_index += len(events)
        return self._flush_result(recorded.get("ids", []), "flushed")

    def flush_all(self) -> Dict[str, Any]:
        events = list(self.audit.events)
        recorded = self.adapter.record_many(events) if events else {"ids": []}
        self.last_flushed_index = len(events)
        return self._flush_result(recorded.get("ids", []), "flushed_all")

    def persisted_status(self) -> Dict[str, Any]:
        adapter_status = self.adapter.status()
        return {
            "ok": True,
            "audit_events": len(self.audit.events),
            "persisted_events": adapter_status.get("events", 0),
            "last_flushed_index": self.last_flushed_index,
            "flushes": len(self.flushes),
        }

    def verify_sync(self) -> Dict[str, Any]:
        status = self.persisted_status()
        status["in_sync"] = status["audit_events"] == status["persisted_events"] == status["last_flushed_index"]
        return status

    def _flush_result(self, ids: List[str], action: str) -> Dict[str, Any]:
        result = {"ok": True, "action": action, "ids": ids, "count": len(ids)}
        self.flushes.append(result)
        if self.kernel is not None and hasattr(self.kernel, "emit"):
            self.kernel.emit("audit_persistence_bridge.flush", result)
        return result

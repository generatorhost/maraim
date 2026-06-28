import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


class SQLiteAuditAdapter:
    """Optional SQLite persistence adapter for runtime audit events.

    This adapter is intentionally narrow: it persists audit events only. It does
    not replace RuntimeStore, RuntimeStorageEngine, or the kernel object graph.
    """

    def __init__(self, path: str = ":memory:", kernel: Any = None):
        self.path = path
        self.kernel = kernel
        self.connection = sqlite3.connect(path)
        self.connection.row_factory = sqlite3.Row
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS audit_events (id TEXT PRIMARY KEY, type TEXT NOT NULL, subject TEXT NOT NULL, action TEXT NOT NULL, status TEXT NOT NULL, metadata_json TEXT NOT NULL, created_at REAL NOT NULL)"
        )
        self.connection.commit()

    def record_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        event_id = event.get("id") or f"audit:{time.time()}"
        metadata_json = json.dumps(event.get("metadata", {}), sort_keys=True)
        self.connection.execute(
            "INSERT OR REPLACE INTO audit_events (id, type, subject, action, status, metadata_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                event_id,
                event.get("type", "runtime"),
                event.get("subject", "unknown"),
                event.get("action", "unknown"),
                event.get("status", "ok"),
                metadata_json,
                event.get("created_at", time.time()),
            ),
        )
        self.connection.commit()
        self._emit("recorded", {"id": event_id})
        return {"ok": True, "id": event_id}

    def record_many(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        ids = [self.record_event(event)["id"] for event in events]
        return {"ok": True, "ids": ids, "count": len(ids)}

    def list_events(self, limit: int = 100) -> Dict[str, Any]:
        rows = self.connection.execute(
            "SELECT id, type, subject, action, status, metadata_json, created_at FROM audit_events ORDER BY created_at ASC LIMIT ?",
            (limit,),
        ).fetchall()
        events = [self._row_to_event(row) for row in rows]
        return {"ok": True, "count": len(events), "events": events}

    def query(self, event_type: Optional[str] = None, status: Optional[str] = None) -> Dict[str, Any]:
        sql = "SELECT id, type, subject, action, status, metadata_json, created_at FROM audit_events"
        clauses = []
        values: List[Any] = []
        if event_type is not None:
            clauses.append("type = ?")
            values.append(event_type)
        if status is not None:
            clauses.append("status = ?")
            values.append(status)
        if clauses:
            sql = sql + " WHERE " + " AND ".join(clauses)
        sql = sql + " ORDER BY created_at ASC"
        rows = self.connection.execute(sql, values).fetchall()
        events = [self._row_to_event(row) for row in rows]
        return {"ok": True, "count": len(events), "events": events}

    def status(self) -> Dict[str, Any]:
        total = self.connection.execute("SELECT COUNT(*) AS count FROM audit_events").fetchone()["count"]
        return {"ok": True, "path": self.path, "events": total}

    def close(self) -> None:
        self.connection.close()

    def _row_to_event(self, row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "id": row["id"],
            "type": row["type"],
            "subject": row["subject"],
            "action": row["action"],
            "status": row["status"],
            "metadata": json.loads(row["metadata_json"]),
            "created_at": row["created_at"],
        }

    def _emit(self, suffix: str, payload: Dict[str, Any]) -> None:
        if self.kernel is not None and hasattr(self.kernel, "emit"):
            self.kernel.emit(f"sqlite_audit_adapter.{suffix}", payload)

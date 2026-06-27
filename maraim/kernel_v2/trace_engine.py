import time
from typing import Any, Dict, List, Optional


class RuntimeTraceEngine:
    """In-memory trace foundation for Kernel v2.

    This engine links execution, artifacts, audit, and metrics snapshots into a
    single trace record. It does not write files, persist databases, call
    networks, or export telemetry.
    """

    def __init__(self, kernel: Any = None):
        self.kernel = kernel
        self.traces: Dict[str, Dict[str, Any]] = {}
        self.events: List[Dict[str, Any]] = []

    def start(self, name: str, subject: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        trace_id = f"trace:{len(self.traces) + 1}"
        trace = {
            "id": trace_id,
            "name": name,
            "subject": subject,
            "metadata": dict(metadata or {}),
            "spans": [],
            "status": "started",
            "started_at": time.time(),
            "ended_at": None,
        }
        self.traces[trace_id] = trace
        self._emit("started", trace)
        return {"ok": True, "trace": trace}

    def add_span(self, trace_id: str, name: str, status: str = "ok", metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        trace = self.traces.get(trace_id)
        if trace is None:
            return {"ok": False, "error": "trace_not_found", "trace": trace_id}
        span = {
            "id": f"{trace_id}:span:{len(trace['spans']) + 1}",
            "name": name,
            "status": status,
            "metadata": dict(metadata or {}),
            "created_at": time.time(),
        }
        trace["spans"].append(span)
        self._emit("span", {"trace": trace_id, "span": span})
        return {"ok": True, "span": span}

    def finish(self, trace_id: str, status: str = "ok", metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        trace = self.traces.get(trace_id)
        if trace is None:
            return {"ok": False, "error": "trace_not_found", "trace": trace_id}
        trace["status"] = status
        trace["ended_at"] = time.time()
        if metadata:
            trace["metadata"].update(metadata)
        self._emit("finished", trace)
        return {"ok": True, "trace": trace}

    def capture_pipeline(self, name: str, run_result: Dict[str, Any], artifact_result: Dict[str, Any], audit_status: Dict[str, Any], metrics_snapshot: Dict[str, Any]) -> Dict[str, Any]:
        run_id = run_result.get("id", "unknown_run")
        started = self.start(name, run_id, {"graph": run_result.get("graph"), "mode": run_result.get("mode")})
        trace_id = started["trace"]["id"]
        self.add_span(trace_id, "execution", "ok" if run_result.get("ok") else "blocked", {"results": len(run_result.get("results", [])), "blocked": len(run_result.get("blocked", []))})
        artifact = artifact_result.get("artifact", {})
        self.add_span(trace_id, "artifact", "ok" if artifact_result.get("ok") else "failed", {"artifact": artifact.get("id"), "permission_summary": artifact.get("permission_summary", {})})
        self.add_span(trace_id, "audit", "ok", {"events": audit_status.get("events", 0), "by_type": audit_status.get("by_type", {})})
        self.add_span(trace_id, "metrics", "ok", {"events": metrics_snapshot.get("events", 0), "counters": len(metrics_snapshot.get("counters", {})), "gauges": len(metrics_snapshot.get("gauges", {}))})
        finished = self.finish(trace_id, "ok" if run_result.get("ok") and artifact_result.get("ok") else "blocked")
        return {"ok": True, "trace": finished["trace"]}

    def get(self, trace_id: str) -> Dict[str, Any]:
        trace = self.traces.get(trace_id)
        if trace is None:
            return {"ok": False, "error": "trace_not_found", "trace": trace_id}
        return {"ok": True, "trace": trace}

    def list(self) -> Dict[str, Any]:
        return {"ok": True, "count": len(self.traces), "traces": list(self.traces.values())}

    def status(self) -> Dict[str, Any]:
        by_status: Dict[str, int] = {}
        for trace in self.traces.values():
            by_status[trace["status"]] = by_status.get(trace["status"], 0) + 1
        return {"traces": len(self.traces), "events": len(self.events), "by_status": by_status}

    def _emit(self, suffix: str, payload: Dict[str, Any]) -> None:
        event = {"type": suffix, "payload": payload, "created_at": time.time()}
        self.events.append(event)
        if self.kernel is not None and hasattr(self.kernel, "emit"):
            self.kernel.emit(f"runtime_trace.{suffix}", event)

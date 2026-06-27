import time
from typing import Any, Dict, Iterable, List, Optional


class RuntimeMetricsEngine:
    """In-memory metrics foundation for Kernel v2.

    This engine records counters, gauges, and timing samples without external
    telemetry, network calls, filesystem writes, or database writes.
    """

    def __init__(self, kernel: Any = None):
        self.kernel = kernel
        self.counters: Dict[str, float] = {}
        self.gauges: Dict[str, float] = {}
        self.timings: Dict[str, List[float]] = {}
        self.events: List[Dict[str, Any]] = []

    def increment(self, name: str, value: float = 1, labels: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        key = self._key(name, labels)
        self.counters[key] = self.counters.get(key, 0) + value
        return self._record("counter", key, self.counters[key], labels)

    def gauge(self, name: str, value: float, labels: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        key = self._key(name, labels)
        self.gauges[key] = value
        return self._record("gauge", key, value, labels)

    def timing(self, name: str, value: float, labels: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        key = self._key(name, labels)
        self.timings.setdefault(key, []).append(value)
        return self._record("timing", key, value, labels)

    def capture_run(self, run_result: Dict[str, Any]) -> Dict[str, Any]:
        run_id = run_result.get("id", "unknown_run")
        results = run_result.get("results", [])
        blocked = run_result.get("blocked", [])
        completed = run_result.get("completed_runtimes", [])
        records = [
            self.increment("execution.runs", 1, {"mode": run_result.get("mode", "unknown"), "ok": str(bool(run_result.get("ok")))}),
            self.gauge("execution.tasks", len(results), {"run": run_id}),
            self.gauge("execution.blocked", len(blocked), {"run": run_id}),
            self.gauge("execution.completed_runtimes", len(completed), {"run": run_id}),
        ]
        return {"ok": True, "records": records, "count": len(records)}

    def capture_audit(self, audit_status: Dict[str, Any]) -> Dict[str, Any]:
        records = [self.gauge("audit.events", audit_status.get("events", 0))]
        for event_type, count in audit_status.get("by_type", {}).items():
            records.append(self.gauge("audit.events.by_type", count, {"type": event_type}))
        for status, count in audit_status.get("by_status", {}).items():
            records.append(self.gauge("audit.events.by_status", count, {"status": status}))
        return {"ok": True, "records": records, "count": len(records)}

    def snapshot(self) -> Dict[str, Any]:
        timing_summary = {}
        for key, values in self.timings.items():
            total = sum(values)
            timing_summary[key] = {"count": len(values), "total": total, "avg": total / len(values) if values else 0}
        return {
            "ok": True,
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "timings": timing_summary,
            "events": len(self.events),
        }

    def status(self) -> Dict[str, Any]:
        return {"counters": len(self.counters), "gauges": len(self.gauges), "timings": len(self.timings), "events": len(self.events)}

    def _key(self, name: str, labels: Optional[Dict[str, Any]] = None) -> str:
        if not labels:
            return name
        suffix = ",".join(f"{key}={labels[key]}" for key in sorted(labels))
        return f"{name}{{{suffix}}}"

    def _record(self, metric_type: str, key: str, value: float, labels: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        event = {"type": metric_type, "key": key, "value": value, "labels": dict(labels or {}), "created_at": time.time()}
        self.events.append(event)
        if self.kernel is not None and hasattr(self.kernel, "emit"):
            self.kernel.emit(f"runtime_metrics.{metric_type}", event)
        return {"ok": True, "metric": event}

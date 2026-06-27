import time
from typing import Any, Dict, List, Optional


class RuntimeReportBuilder:
    """In-memory report builder foundation for Kernel v2.

    Builds deterministic status reports from trace, metrics, audit, artifact,
    and execution summaries without writing files or calling external systems.
    """

    def __init__(self, kernel: Any = None):
        self.kernel = kernel
        self.reports: Dict[str, Dict[str, Any]] = {}

    def build_report(
        self,
        title: str,
        run_result: Optional[Dict[str, Any]] = None,
        artifact_summary: Optional[Dict[str, Any]] = None,
        audit_status: Optional[Dict[str, Any]] = None,
        metrics_snapshot: Optional[Dict[str, Any]] = None,
        trace_status: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        report_id = f"report:{len(self.reports) + 1}"
        report = {
            "id": report_id,
            "title": title,
            "sections": [],
            "created_at": time.time(),
        }
        if run_result is not None:
            report["sections"].append(self._execution_section(run_result))
        if artifact_summary is not None:
            report["sections"].append({"name": "artifact", "summary": artifact_summary})
        if audit_status is not None:
            report["sections"].append({"name": "audit", "summary": audit_status})
        if metrics_snapshot is not None:
            report["sections"].append({"name": "metrics", "summary": self._metrics_summary(metrics_snapshot)})
        if trace_status is not None:
            report["sections"].append({"name": "trace", "summary": trace_status})
        self.reports[report_id] = report
        if self.kernel is not None and hasattr(self.kernel, "emit"):
            self.kernel.emit("runtime_report.created", report)
        return {"ok": True, "report": report}

    def render_text(self, report_id: str) -> Dict[str, Any]:
        report = self.reports.get(report_id)
        if report is None:
            return {"ok": False, "error": "report_not_found", "report": report_id}
        lines: List[str] = [report["title"], "=" * len(report["title"]), ""]
        for section in report.get("sections", []):
            lines.append(section["name"].upper())
            lines.append(str(section.get("summary", {})))
            lines.append("")
        return {"ok": True, "report": report_id, "text": "\n".join(lines).rstrip()}

    def get(self, report_id: str) -> Dict[str, Any]:
        report = self.reports.get(report_id)
        if report is None:
            return {"ok": False, "error": "report_not_found", "report": report_id}
        return {"ok": True, "report": report}

    def status(self) -> Dict[str, Any]:
        return {"reports": len(self.reports), "last": list(self.reports.values())[-1] if self.reports else None}

    def _execution_section(self, run_result: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "name": "execution",
            "summary": {
                "run": run_result.get("id"),
                "ok": run_result.get("ok"),
                "mode": run_result.get("mode"),
                "results": len(run_result.get("results", [])),
                "blocked": len(run_result.get("blocked", [])),
                "completed_runtimes": len(run_result.get("completed_runtimes", [])),
            },
        }

    def _metrics_summary(self, metrics_snapshot: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "counters": len(metrics_snapshot.get("counters", {})),
            "gauges": len(metrics_snapshot.get("gauges", {})),
            "timings": len(metrics_snapshot.get("timings", {})),
            "events": metrics_snapshot.get("events", 0),
        }

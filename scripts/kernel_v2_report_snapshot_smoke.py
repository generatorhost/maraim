import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from maraim.kernel_v2 import KernelV2, RuntimeReportBuilder, RuntimeSnapshotBuilder

kernel = KernelV2(dna_root="dna")
reports = RuntimeReportBuilder(kernel)
snapshots = RuntimeSnapshotBuilder(kernel)

run_result = {
    "id": "run:report_snapshot:1",
    "ok": True,
    "mode": "simulated",
    "results": [{"task": "task.1"}],
    "blocked": [],
    "completed_runtimes": ["runtime.sample@1.0.0"],
}
artifact_summary = {"ok": True, "artifact": "artifact.1", "permission_summary": {"allowed": 1, "blocked": 0}}
audit_status = {"events": 2, "by_type": {"execution": 1, "artifact": 1}}
metrics_snapshot = {"ok": True, "counters": {"execution.runs": 1}, "gauges": {"audit.events": 2}, "timings": {}, "events": 3}
trace_status = {"traces": 1, "events": 4, "by_status": {"ok": 1}}

report = reports.build_report("Phase 2 Runtime Report", run_result, artifact_summary, audit_status, metrics_snapshot, trace_status)
report_id = report["report"]["id"]
rendered = reports.render_text(report_id)
missing_report = reports.get("missing.report")
report_status = reports.status()

before = snapshots.build_snapshot("before", {"runtimes": 1}, {"runs": 0}, {"artifacts": 0}, {"events": 0}, {"events": 0}, {"traces": 0})
after = snapshots.build_snapshot("after", {"runtimes": 2}, {"runs": 1}, {"artifacts": 1}, audit_status, {"events": 3}, trace_status)
comparison = snapshots.compare(before["snapshot"]["id"], after["snapshot"]["id"])
missing_snapshot = snapshots.get("missing.snapshot")
snapshot_status = snapshots.status()

print("MARAIM_REPORT_SNAPSHOT_SMOKE_OK")
print(rendered)
print(snapshot_status)

assert report["ok"] is True
assert rendered["ok"] is True
assert "Phase 2 Runtime Report" in rendered["text"]
assert missing_report["ok"] is False
assert report_status["reports"] >= 1
assert before["ok"] is True
assert after["ok"] is True
assert comparison["ok"] is True
assert comparison["diff"]["execution"]["after"]["runs"] == 1
assert missing_snapshot["ok"] is False
assert snapshot_status["snapshots"] >= 2

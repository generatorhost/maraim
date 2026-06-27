import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from maraim.kernel_v2 import KernelV2, RuntimeMetricsEngine, RuntimeTraceEngine

kernel = KernelV2(dna_root="dna")
metrics = RuntimeMetricsEngine(kernel)
trace = RuntimeTraceEngine(kernel)

run_result = {
    "id": "run:trace_smoke:1",
    "graph": "task_graph:trace_smoke:1",
    "mode": "simulated",
    "ok": True,
    "results": [
        {"task": "task.1", "runtime": "plugins.sample@1.0.0", "status": "completed", "ready": True, "permissions": {"can_execute": True, "missing": []}}
    ],
    "blocked": [],
    "completed_runtimes": ["plugins.sample@1.0.0"],
}
artifact_result = {
    "ok": True,
    "artifact": {
        "id": "trace_artifact.1",
        "run": run_result["id"],
        "permission_summary": {"allowed": 1, "blocked": 0, "missing": {}},
    },
}
audit_status = {"events": 2, "by_type": {"execution": 1, "artifact": 1}, "by_status": {"ok": 2}}
metrics.capture_run(run_result)
metrics.capture_audit(audit_status)
metrics_snapshot = metrics.snapshot()

manual_start = trace.start("manual_trace", "manual_subject")
manual_span = trace.add_span(manual_start["trace"]["id"], "manual_span", "ok", {"sample": True})
manual_finish = trace.finish(manual_start["trace"]["id"], "ok")
trace_result = trace.capture_pipeline("trace_smoke", run_result, artifact_result, audit_status, metrics_snapshot)
trace_id = trace_result["trace"]["id"]
loaded = trace.get(trace_id)
listed = trace.list()
missing = trace.get("missing.trace")
status = trace.status()

print("MARAIM_TRACE_ENGINE_SMOKE_OK")
print(trace_result)
print(status)

assert manual_start["ok"] is True
assert manual_span["ok"] is True
assert manual_finish["ok"] is True
assert trace_result["ok"] is True
assert trace_result["trace"]["status"] == "ok"
assert len(trace_result["trace"]["spans"]) >= 4
assert loaded["ok"] is True
assert listed["count"] >= 2
assert missing["ok"] is False
assert status["traces"] >= 2
assert status["events"] >= 8
assert status["by_status"]["ok"] >= 2

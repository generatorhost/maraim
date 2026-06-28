import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from maraim.kernel_v2 import KernelV2, RuntimeAuditTrail, SQLiteAuditAdapter

kernel = KernelV2(dna_root="dna")
audit = RuntimeAuditTrail(kernel)
sqlite = SQLiteAuditAdapter(":memory:", kernel)

manual = audit.record("execution", "run.sqlite.1", "run", "ok", {"mode": "smoke"})
artifact = audit.record("artifact", "artifact.sqlite.1", "capture", "ok", {"run": "run.sqlite.1"})
recorded = sqlite.record_many([manual["event"], artifact["event"]])
listed = sqlite.list_events()
execution = sqlite.query(event_type="execution")
ok_status = sqlite.query(status="ok")
status = sqlite.status()
sqlite.close()

print("MARAIM_SQLITE_AUDIT_ADAPTER_SMOKE_OK")
print(status)

assert manual["ok"] is True
assert artifact["ok"] is True
assert recorded["ok"] is True
assert recorded["count"] == 2
assert listed["ok"] is True and listed["count"] == 2
assert execution["ok"] is True and execution["count"] == 1
assert ok_status["ok"] is True and ok_status["count"] == 2
assert status["ok"] is True and status["events"] == 2

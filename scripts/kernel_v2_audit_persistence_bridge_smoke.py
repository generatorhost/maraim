import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from maraim.kernel_v2 import AuditPersistenceBridge, KernelV2, RuntimeAuditTrail, SQLiteAuditAdapter

kernel = KernelV2(dna_root="dna")
audit = RuntimeAuditTrail(kernel)
sqlite = SQLiteAuditAdapter(":memory:", kernel)
bridge = AuditPersistenceBridge(audit, sqlite, kernel)

empty_flush = bridge.flush_new()
audit.record("execution", "run.bridge.1", "run", "ok", {"mode": "bridge_smoke"})
audit.record("artifact", "artifact.bridge.1", "capture", "ok", {"run": "run.bridge.1"})
first_flush = bridge.flush_new()
second_flush = bridge.flush_new()
sync = bridge.verify_sync()
listed = sqlite.list_events()
audit.record("metrics", "metrics.bridge.1", "capture", "ok", {"events": 2})
third_flush = bridge.flush_new()
final_sync = bridge.verify_sync()
sqlite.close()

print("MARAIM_AUDIT_PERSISTENCE_BRIDGE_SMOKE_OK")
print(final_sync)

assert empty_flush["count"] == 0
assert first_flush["count"] == 2
assert second_flush["count"] == 0
assert sync["in_sync"] is True
assert listed["count"] == 2
assert third_flush["count"] == 1
assert final_sync["in_sync"] is True
assert final_sync["audit_events"] == 3
assert final_sync["persisted_events"] == 3

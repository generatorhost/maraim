import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from maraim.kernel_v2 import (
    AuditPersistenceBridge,
    KernelV2,
    PersistenceCheckpoint,
    PersistenceHealth,
    RuntimeAuditTrail,
    SQLiteAuditAdapter,
)

kernel = KernelV2(dna_root="dna")
audit = RuntimeAuditTrail(kernel)
sqlite = SQLiteAuditAdapter(":memory:", kernel)
bridge = AuditPersistenceBridge(audit, sqlite, kernel)
health = PersistenceHealth(kernel)
checkpoints = PersistenceCheckpoint(kernel)

initial_health = health.audit_bridge_health(bridge)
checkpoint_before = checkpoints.capture_audit_bridge(bridge, "before")
audit.record("execution", "run.persistence.1", "run", "ok", {"mode": "health_checkpoint_smoke"})
audit.record("artifact", "artifact.persistence.1", "capture", "ok", {"run": "run.persistence.1"})
bridge.flush_new()
final_health = health.audit_bridge_health(bridge)
checkpoint_after = checkpoints.capture_audit_bridge(bridge, "after")
comparison = checkpoints.compare(checkpoint_before["checkpoint"]["id"], checkpoint_after["checkpoint"]["id"])
missing_compare = checkpoints.compare("missing.before", checkpoint_after["checkpoint"]["id"])
health_summary = health.status()
checkpoint_summary = checkpoints.status()
sqlite.close()

print("MARAIM_PERSISTENCE_HEALTH_CHECKPOINT_SMOKE_OK")
print(health_summary)
print(checkpoint_summary)

assert initial_health["check"]["ok"] is True
assert final_health["check"]["ok"] is True
assert checkpoint_before["ok"] is True
assert checkpoint_after["ok"] is True
assert comparison["ok"] is True
assert comparison["changed"] is True
assert missing_compare["ok"] is False
assert health_summary["ok"] is True
assert health_summary["checks"] == 2
assert checkpoint_summary["ok"] is True
assert checkpoint_summary["checkpoints"] == 2

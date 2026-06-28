import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from maraim.kernel_v2 import (
    AuditPersistenceBridge,
    KernelV2,
    PersistenceRecovery,
    RuntimeAuditTrail,
    SQLiteAuditAdapter,
)

kernel = KernelV2(dna_root="dna")
audit = RuntimeAuditTrail(kernel)
sqlite = SQLiteAuditAdapter(":memory:", kernel)
bridge = AuditPersistenceBridge(audit, sqlite, kernel)
recovery = PersistenceRecovery(kernel)

clean_plan = recovery.inspect_audit_bridge(bridge)
clean_recovery = recovery.recover_audit_bridge(bridge)
audit.record("execution", "run.recovery.1", "run", "ok", {"mode": "recovery_smoke"})
audit.record("artifact", "artifact.recovery.1", "capture", "ok", {"run": "run.recovery.1"})
dirty_plan = recovery.inspect_audit_bridge(bridge)
dirty_recovery = recovery.recover_audit_bridge(bridge)
final_plan = recovery.inspect_audit_bridge(bridge)
status = recovery.status()
sqlite.close()

print("MARAIM_PERSISTENCE_RECOVERY_SMOKE_OK")
print(status)

assert clean_plan["plan"]["action"] == "none"
assert clean_recovery["recovered"] is False
assert dirty_plan["plan"]["action"] == "flush_new"
assert dirty_plan["plan"]["gap"] == 2
assert dirty_recovery["ok"] is True
assert dirty_recovery["recovered"] is True
assert dirty_recovery["after"]["in_sync"] is True
assert final_plan["plan"]["action"] == "none"
assert status["actions"] >= 4

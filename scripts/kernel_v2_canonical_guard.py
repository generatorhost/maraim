from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

canonical = ROOT / "scripts/kernel_v2_all_smoke.py"
phase4_smoke = ROOT / "scripts/kernel_v2_phase4_foundation_smoke.py"
init_file = ROOT / "maraim/kernel_v2/__init__.py"
real_adapters = ROOT / "maraim/kernel_v2/real_adapters_foundation.py"
sandbox_enforcement = ROOT / "maraim/kernel_v2/sandbox_enforcement_foundation.py"
sqlite_audit = ROOT / "maraim/kernel_v2/sqlite_audit_adapter.py"
audit_bridge = ROOT / "maraim/kernel_v2/audit_persistence_bridge.py"
persistence_health = ROOT / "maraim/kernel_v2/persistence_health.py"
persistence_status = ROOT / "maraim/kernel_v2/persistence_status.py"
persistence_checkpoint = ROOT / "maraim/kernel_v2/persistence_checkpoint.py"
persistence_recovery = ROOT / "maraim/kernel_v2/persistence_recovery.py"

required_smokes = [
    "scripts/kernel_v2_smoke.py",
    "scripts/kernel_v2_runtime_systems_smoke.py",
    "scripts/kernel_v2_runtime_store_smoke.py",
    "scripts/kernel_v2_hot_reload_smoke.py",
    "scripts/kernel_v2_mount_manager_smoke.py",
    "scripts/kernel_v2_storage_health_smoke.py",
    "scripts/kernel_v2_source_adapters_smoke.py",
    "scripts/kernel_v2_dependency_resolver_v2_smoke.py",
    "scripts/kernel_v2_task_graph_v2_smoke.py",
    "scripts/kernel_v2_execution_adapter_v2_smoke.py",
    "scripts/kernel_v2_result_artifact_v2_smoke.py",
    "scripts/kernel_v2_permission_sandbox_smoke.py",
    "scripts/kernel_v2_audit_trail_smoke.py",
    "scripts/kernel_v2_metrics_engine_smoke.py",
    "scripts/kernel_v2_trace_engine_smoke.py",
    "scripts/kernel_v2_report_snapshot_smoke.py",
    "scripts/kernel_v2_phase3_foundation_smoke.py",
    "scripts/kernel_v2_phase4_foundation_smoke.py",
    "scripts/kernel_v2_real_adapters_foundation_smoke.py",
    "scripts/kernel_v2_sandbox_enforcement_foundation_smoke.py",
    "scripts/kernel_v2_sqlite_audit_adapter_smoke.py",
    "scripts/kernel_v2_audit_persistence_bridge_smoke.py",
    "scripts/kernel_v2_persistence_status_checkpoint_smoke.py",
    "scripts/kernel_v2_persistence_recovery_smoke.py",
]

transition_gates = [
    "scripts/kernel_v2_phase2_plus_smoke.py",
    "scripts/kernel_v2_phase2_plus2_smoke.py",
    "scripts/kernel_v2_phase2_plus3_smoke.py",
    "scripts/kernel_v2_phase2_plus4_smoke.py",
]

required_files = [canonical, phase4_smoke, init_file, real_adapters, sandbox_enforcement, sqlite_audit, audit_bridge, persistence_health, persistence_checkpoint, persistence_recovery]
missing = [str(path.relative_to(ROOT)) for path in required_files if not path.exists()]
canonical_text = canonical.read_text(encoding="utf-8") if canonical.exists() else ""
phase4_text = phase4_smoke.read_text(encoding="utf-8") if phase4_smoke.exists() else ""
init_text = init_file.read_text(encoding="utf-8") if init_file.exists() else ""
real_adapters_text = real_adapters.read_text(encoding="utf-8") if real_adapters.exists() else ""
sandbox_enforcement_text = sandbox_enforcement.read_text(encoding="utf-8") if sandbox_enforcement.exists() else ""

violations = []
for smoke in required_smokes:
    if smoke not in canonical_text:
        violations.append(f"canonical_gate_missing:{smoke}")
for gate in transition_gates:
    if gate in canonical_text:
        violations.append(f"canonical_gate_uses_transition_gate:{gate}")
if persistence_status.exists():
    violations.append("deprecated_persistence_status_file_exists")
if "PersistenceStatus" in init_text:
    violations.append("deprecated_persistence_status_exported")
if "from maraim.kernel_v2 import KernelV2, PHASE4_STAGES, Phase4FoundationEngine" not in phase4_text:
    violations.append("phase4_smoke_does_not_use_public_api")
if "from .phase4_foundation import Phase4FoundationEngine, PHASE4_STAGES" not in init_text:
    violations.append("phase4_not_exported_from_public_api")
if "from .real_adapters_foundation import RealAdapterFoundation" not in init_text:
    violations.append("real_adapters_not_exported_from_public_api")
if "from .sandbox_enforcement_foundation import SandboxEnforcementFoundation" not in init_text:
    violations.append("sandbox_enforcement_not_exported_from_public_api")
if "from .sqlite_audit_adapter import SQLiteAuditAdapter" not in init_text:
    violations.append("sqlite_audit_not_exported_from_public_api")
if "from .audit_persistence_bridge import AuditPersistenceBridge" not in init_text:
    violations.append("audit_persistence_bridge_not_exported_from_public_api")
if "from .persistence_health import PersistenceHealth" not in init_text:
    violations.append("persistence_health_not_exported_from_public_api")
if "from .persistence_checkpoint import PersistenceCheckpoint" not in init_text:
    violations.append("persistence_checkpoint_not_exported_from_public_api")
if "from .persistence_recovery import PersistenceRecovery" not in init_text:
    violations.append("persistence_recovery_not_exported_from_public_api")
if "maraim.kernel_v2.phase4_foundation" in phase4_text:
    violations.append("phase4_smoke_uses_deep_import")
for label, text in [("real_adapters", real_adapters_text), ("sandbox_enforcement", sandbox_enforcement_text)]:
    for token in ["import subprocess", "import requests", "import sqlite3", "open(", ".write_text(", ".write_bytes("]:
        if token in text:
            violations.append(f"{label}_forbidden_token:{token}")

print("MARAIM_KERNEL_V2_CANONICAL_GUARD_OK")
print({"missing": missing, "violations": violations})
assert not missing, missing
assert not violations, violations

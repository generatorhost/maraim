from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

canonical = ROOT / "scripts/kernel_v2_all_smoke.py"
phase4_smoke = ROOT / "scripts/kernel_v2_phase4_foundation_smoke.py"
init_file = ROOT / "maraim/kernel_v2/__init__.py"

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
]

transition_gates = [
    "scripts/kernel_v2_phase2_plus_smoke.py",
    "scripts/kernel_v2_phase2_plus2_smoke.py",
    "scripts/kernel_v2_phase2_plus3_smoke.py",
    "scripts/kernel_v2_phase2_plus4_smoke.py",
]

missing = [str(path.relative_to(ROOT)) for path in [canonical, phase4_smoke, init_file] if not path.exists()]
canonical_text = canonical.read_text(encoding="utf-8") if canonical.exists() else ""
phase4_text = phase4_smoke.read_text(encoding="utf-8") if phase4_smoke.exists() else ""
init_text = init_file.read_text(encoding="utf-8") if init_file.exists() else ""

violations = []
for smoke in required_smokes:
    if smoke not in canonical_text:
        violations.append(f"canonical_gate_missing:{smoke}")
for gate in transition_gates:
    if gate in canonical_text:
        violations.append(f"canonical_gate_uses_transition_gate:{gate}")
if "from maraim.kernel_v2 import KernelV2, PHASE4_STAGES, Phase4FoundationEngine" not in phase4_text:
    violations.append("phase4_smoke_does_not_use_public_api")
if "from .phase4_foundation import Phase4FoundationEngine, PHASE4_STAGES" not in init_text:
    violations.append("phase4_not_exported_from_public_api")
if "maraim.kernel_v2.phase4_foundation" in phase4_text:
    violations.append("phase4_smoke_uses_deep_import")

print("MARAIM_KERNEL_V2_CANONICAL_GUARD_OK")
print({"missing": missing, "violations": violations})
assert not missing, missing
assert not violations, violations

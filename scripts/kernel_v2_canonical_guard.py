from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

canonical = ROOT / "scripts/kernel_v2_all_smoke.py"
phase4_smoke = ROOT / "scripts/kernel_v2_phase4_foundation_smoke.py"
init_file = ROOT / "maraim/kernel_v2/__init__.py"

missing = [str(path.relative_to(ROOT)) for path in [canonical, phase4_smoke, init_file] if not path.exists()]
canonical_text = canonical.read_text(encoding="utf-8") if canonical.exists() else ""
phase4_text = phase4_smoke.read_text(encoding="utf-8") if phase4_smoke.exists() else ""
init_text = init_file.read_text(encoding="utf-8") if init_file.exists() else ""

violations = []
if "scripts/kernel_v2_phase2_plus4_smoke.py" not in canonical_text:
    violations.append("canonical_gate_does_not_call_latest_plus4")
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

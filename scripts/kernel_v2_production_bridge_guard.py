from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

required = [
    ROOT / "maraim/kernel_v2/production_bridge/__init__.py",
    ROOT / "maraim/kernel_v2/production_bridge/steps.py",
    ROOT / "scripts/kernel_v2_production_bridge_steps_smoke.py",
]
missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
init_text = (ROOT / "maraim/kernel_v2/__init__.py").read_text(encoding="utf-8")
ci_text = (ROOT / "scripts/kernel_v2_ci_gate.py").read_text(encoding="utf-8")
violations = []
if "from .production_bridge import ProductionBridgeSteps" not in init_text:
    violations.append("production_bridge_not_exported")
if "scripts/kernel_v2_production_bridge_steps_smoke.py" not in ci_text:
    violations.append("production_bridge_smoke_not_in_ci_gate")
print("MARAIM_PRODUCTION_BRIDGE_GUARD_OK")
print({"missing": missing, "violations": violations})
assert not missing, missing
assert not violations, violations

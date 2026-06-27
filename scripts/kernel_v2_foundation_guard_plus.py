from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1]

runpy.run_path(str(ROOT / "scripts/kernel_v2_foundation_guard.py"), run_name="__main__")

extra_module = ROOT / "maraim/kernel_v2/trace_engine.py"
extra_smoke = ROOT / "scripts/kernel_v2_trace_engine_smoke.py"
phase2_plus = (ROOT / "scripts/kernel_v2_phase2_plus_smoke.py").read_text(encoding="utf-8")
content = extra_module.read_text(encoding="utf-8")
forbidden = ["import subprocess", "import requests", "import sqlite3", "open(", ".write_text(", ".write_bytes("]
violations = [token for token in forbidden if token in content]

print("MARAIM_KERNEL_V2_FOUNDATION_GUARD_PLUS_OK")
print({"trace_module": extra_module.exists(), "trace_smoke": extra_smoke.exists(), "in_plus_gate": "scripts/kernel_v2_trace_engine_smoke.py" in phase2_plus, "violations": violations})

assert extra_module.exists()
assert extra_smoke.exists()
assert "scripts/kernel_v2_trace_engine_smoke.py" in phase2_plus
assert not violations, violations

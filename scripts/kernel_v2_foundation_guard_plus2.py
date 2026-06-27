from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1]

runpy.run_path(str(ROOT / "scripts/kernel_v2_foundation_guard_plus.py"), run_name="__main__")
extra_files = [
    "maraim/kernel_v2/report_builder.py",
    "maraim/kernel_v2/snapshot_builder.py",
    "scripts/kernel_v2_report_snapshot_smoke.py",
]
forbidden = ["import subprocess", "import requests", "import sqlite3", "open(", ".write_text(", ".write_bytes("]
violations = []
missing = []
for relative_path in extra_files:
    path = ROOT / relative_path
    if not path.exists():
        missing.append(relative_path)
        continue
    content = path.read_text(encoding="utf-8")
    for token in forbidden:
        if token in content:
            violations.append({"file": relative_path, "token": token})

plus_gate = (ROOT / "scripts/kernel_v2_phase2_plus2_smoke.py").read_text(encoding="utf-8")
missing_from_gate = ["scripts/kernel_v2_report_snapshot_smoke.py"] if "scripts/kernel_v2_report_snapshot_smoke.py" not in plus_gate else []

print("MARAIM_KERNEL_V2_FOUNDATION_GUARD_PLUS2_OK")
print({"missing": missing, "missing_from_gate": missing_from_gate, "violations": violations})
assert not missing, missing
assert not missing_from_gate, missing_from_gate
assert not violations, violations

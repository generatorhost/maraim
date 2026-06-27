from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1]
runpy.run_path(str(ROOT / "scripts/kernel_v2_foundation_guard_plus2.py"), run_name="__main__")

files = [
    ROOT / "maraim/kernel_v2/phase3_foundation.py",
    ROOT / "scripts/kernel_v2_phase3_foundation_smoke.py",
]
violations = []
for path in files:
    content = path.read_text(encoding="utf-8")
    for token in ["import subprocess", "import requests", "import sqlite3", "open(", ".write_text(", ".write_bytes("]:
        if token in content:
            violations.append({"file": str(path), "token": token})

print("MARAIM_KERNEL_V2_FOUNDATION_GUARD_PLUS3_OK")
print({"files": [path.exists() for path in files], "violations": violations})
assert all(path.exists() for path in files)
assert not violations, violations

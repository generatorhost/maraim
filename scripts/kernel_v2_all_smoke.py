import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SMOKE_TESTS = [
    "scripts/kernel_v2_smoke.py",
    "scripts/kernel_v2_runtime_systems_smoke.py",
]


def run_smoke(relative_path: str) -> dict:
    script = ROOT / relative_path
    if not script.exists():
        return {"ok": False, "script": relative_path, "error": "script_not_found"}
    runpy.run_path(str(script), run_name="__main__")
    return {"ok": True, "script": relative_path}


results = [run_smoke(path) for path in SMOKE_TESTS]
failed = [item for item in results if not item["ok"]]

print("MARAIM_KERNEL_V2_ALL_SMOKE_OK" if not failed else "MARAIM_KERNEL_V2_ALL_SMOKE_FAILED")
print(results)

assert not failed, failed

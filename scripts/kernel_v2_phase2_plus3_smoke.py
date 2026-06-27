import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SMOKE_TESTS = [
    "scripts/kernel_v2_phase2_plus2_smoke.py",
    "scripts/kernel_v2_phase3_foundation_smoke.py",
]

results = []
for relative_path in SMOKE_TESTS:
    script = ROOT / relative_path
    if not script.exists():
        results.append({"ok": False, "script": relative_path, "error": "script_not_found"})
    else:
        runpy.run_path(str(script), run_name="__main__")
        results.append({"ok": True, "script": relative_path})

failed = [item for item in results if not item["ok"]]
print("MARAIM_KERNEL_V2_PHASE2_PLUS3_SMOKE_OK" if not failed else "MARAIM_KERNEL_V2_PHASE2_PLUS3_SMOKE_FAILED")
print(results)
assert not failed, failed

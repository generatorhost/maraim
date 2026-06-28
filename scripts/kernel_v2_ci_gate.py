import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

GATES = [
    "scripts/kernel_v2_canonical_guard.py",
    "scripts/kernel_v2_all_smoke.py",
    "scripts/kernel_v2_real_source_readiness_smoke.py",
]

results = []
for relative_path in GATES:
    script = ROOT / relative_path
    if not script.exists():
        results.append({"ok": False, "script": relative_path, "error": "script_not_found"})
    else:
        runpy.run_path(str(script), run_name="__main__")
        results.append({"ok": True, "script": relative_path})

failed = [item for item in results if not item["ok"]]
print("MARAIM_KERNEL_V2_CI_GATE_OK" if not failed else "MARAIM_KERNEL_V2_CI_GATE_FAILED")
print(results)
assert not failed, failed

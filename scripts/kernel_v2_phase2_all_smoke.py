import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SMOKE_TESTS = [
    "scripts/kernel_v2_smoke.py",
    "scripts/kernel_v2_runtime_systems_smoke.py",
    "scripts/kernel_v2_runtime_store_smoke.py",
    "scripts/kernel_v2_hot_reload_smoke.py",
    "scripts/kernel_v2_mount_manager_smoke.py",
    "scripts/kernel_v2_storage_health_smoke.py",
    "scripts/kernel_v2_source_adapters_smoke.py",
    "scripts/kernel_v2_dependency_resolver_v2_smoke.py",
    "scripts/kernel_v2_task_graph_v2_smoke.py",
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
print("MARAIM_KERNEL_V2_PHASE2_ALL_SMOKE_OK" if not failed else "MARAIM_KERNEL_V2_PHASE2_ALL_SMOKE_FAILED")
print(results)
assert not failed, failed

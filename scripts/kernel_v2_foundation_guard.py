from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FOUNDATION_MODULES = [
    "maraim/kernel_v2/runtime_systems.py",
    "maraim/kernel_v2/runtime_store.py",
    "maraim/kernel_v2/hot_reload.py",
    "maraim/kernel_v2/mount_manager.py",
    "maraim/kernel_v2/storage_engine.py",
    "maraim/kernel_v2/health_engine.py",
    "maraim/kernel_v2/source_adapters.py",
    "maraim/kernel_v2/dependency_resolver_v2.py",
    "maraim/kernel_v2/task_graph_v2.py",
    "maraim/kernel_v2/execution_adapter_v2.py",
    "maraim/kernel_v2/result_artifact_v2.py",
    "maraim/kernel_v2/permission_sandbox.py",
    "maraim/kernel_v2/audit_trail.py",
]

EXPECTED_SMOKES = [
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
]

FORBIDDEN_TOKENS = [
    "import subprocess",
    "from subprocess",
    "import requests",
    "from requests",
    "import urllib",
    "from urllib",
    "import httpx",
    "from httpx",
    "import sqlite3",
    "import psycopg2",
    "import asyncpg",
    "import socket",
    "from socket",
    "Path.write_text",
    "Path.write_bytes",
    ".write_text(",
    ".write_bytes(",
    "open(",
]

missing_modules = [path for path in FOUNDATION_MODULES if not (ROOT / path).exists()]
missing_smokes = [path for path in EXPECTED_SMOKES if not (ROOT / path).exists()]
violations = []

for relative_path in FOUNDATION_MODULES:
    path = ROOT / relative_path
    if not path.exists():
        continue
    content = path.read_text(encoding="utf-8")
    for token in FORBIDDEN_TOKENS:
        if token in content:
            violations.append({"file": relative_path, "token": token})

phase2_gate = (ROOT / "scripts/kernel_v2_phase2_all_smoke.py").read_text(encoding="utf-8")
missing_from_gate = [path for path in EXPECTED_SMOKES if path not in phase2_gate]

print("MARAIM_KERNEL_V2_FOUNDATION_GUARD_OK")
print({
    "modules": len(FOUNDATION_MODULES),
    "smokes": len(EXPECTED_SMOKES),
    "missing_modules": missing_modules,
    "missing_smokes": missing_smokes,
    "missing_from_gate": missing_from_gate,
    "violations": violations,
})

assert not missing_modules, missing_modules
assert not missing_smokes, missing_smokes
assert not missing_from_gate, missing_from_gate
assert not violations, violations

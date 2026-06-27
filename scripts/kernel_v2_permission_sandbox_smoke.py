import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from maraim.kernel_v2 import KernelV2, PermissionSandbox

kernel = KernelV2(dna_root="dna")
sandbox = PermissionSandbox(kernel)
runtime_id = "plugins.sample.freelance_plugin@1.0.0"

grant = sandbox.grant(runtime_id, ["execute_simulated", "read_runtime_store"], reason="smoke_grant")
deny = sandbox.deny(runtime_id, ["network_access", "process_spawn"], reason="smoke_deny")
allowed = sandbox.evaluate(runtime_id, "execute_simulated")
blocked = sandbox.evaluate(runtime_id, "network_access")
required_ok = sandbox.require(runtime_id, ["execute_simulated", "read_runtime_store"])
required_missing = sandbox.require(runtime_id, ["execute_simulated", "network_access"])
plan_ok = sandbox.build_plan(runtime_id, ["execute_simulated", "read_runtime_store"])
plan_blocked = sandbox.build_plan(runtime_id, ["execute_simulated", "process_spawn"])
status = sandbox.status()

print("MARAIM_PERMISSION_SANDBOX_SMOKE_OK")
print(plan_ok)
print(plan_blocked)
print(status)

assert grant["ok"] is True
assert deny["ok"] is True
assert allowed["allowed"] is True
assert blocked["allowed"] is False
assert required_ok["ok"] is True
assert required_missing["ok"] is False
assert "network_access" in required_missing["missing"]
assert plan_ok["can_execute"] is True
assert plan_blocked["can_execute"] is False
assert "process_spawn" in plan_blocked["missing"]
assert status["grant_subjects"] >= 1
assert status["deny_subjects"] >= 1
assert status["decisions"] >= 6

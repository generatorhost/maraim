import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from maraim.kernel_v2 import KernelV2, RuntimeExecutionGate, RuntimeWorkspaceManager, SandboxEnforcementFoundation

kernel = KernelV2(dna_root="dna")
workspaces = RuntimeWorkspaceManager(kernel=kernel)
sandbox = SandboxEnforcementFoundation(kernel)
workspaces.create_workspace("exec_ws_001", "git")
sandbox.define_profile("safe.profile", allowed=["manifest_prepare"], denied=["real_clone"])

gate = RuntimeExecutionGate(workspaces, sandbox, kernel)
missing_ws = gate.evaluate("missing_ws", "safe.profile", ["manifest_prepare"], "git_adapter")
allowed = gate.evaluate("exec_ws_001", "safe.profile", ["manifest_prepare"], "git_adapter")
blocked = gate.evaluate("exec_ws_001", "safe.profile", ["real_clone"], "git_adapter")
bound = gate.bind_if_allowed("exec_ws_001", "safe.profile", ["manifest_prepare"], "git_adapter", "repo-alpha")
not_bound = gate.bind_if_allowed("exec_ws_001", "safe.profile", ["real_clone"], "git_adapter", "repo-alpha")
status = gate.status()
workspace_status = workspaces.status()

print("MARAIM_RUNTIME_EXECUTION_GATE_SMOKE_OK")
print(status)

assert missing_ws["allowed"] is False
assert allowed["allowed"] is True
assert blocked["allowed"] is False
assert bound["bound"] is True
assert not_bound["bound"] is False
assert status["decisions"] == 5
assert status["allowed"] == 2
assert status["blocked"] == 3
assert workspace_status["bindings"] == 1

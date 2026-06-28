import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from maraim.kernel_v2 import KernelV2, RuntimeWorkspaceManager

kernel = KernelV2(dna_root="dna")
manager = RuntimeWorkspaceManager(kernel=kernel)
created = manager.create_workspace("git_adapter_001", "git")
duplicate = manager.create_workspace("git_adapter_001", "git")
unsafe = manager.create_workspace("../escape", "bad")
spaced = manager.create_workspace(" bad ", "bad")
binding = manager.bind("git_adapter_001", "git_adapter", "repo-alpha")
missing_binding = manager.bind("missing", "git_adapter", "repo-alpha")
marked = manager.mark("git_adapter_001", "ready")
status = manager.status()

print("MARAIM_RUNTIME_WORKSPACE_MANAGER_SMOKE_OK")
print(status)

assert created["ok"] is True
assert duplicate["ok"] is False
assert unsafe["ok"] is False
assert spaced["ok"] is False
assert binding["ok"] is True
assert missing_binding["ok"] is False
assert marked["ok"] is True
assert status["ok"] is True
assert status["workspaces"] == 1
assert status["bindings"] == 1
assert status["items"][0]["status"] == "ready"

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from maraim.kernel_v2 import KernelV2, RealAdapterFoundation, SandboxEnforcementFoundation

kernel = KernelV2(dna_root="dna")
adapters = RealAdapterFoundation(kernel)
sandbox = SandboxEnforcementFoundation(kernel)

profile = sandbox.define_profile(
    "foundation.safe",
    allowed=["manifest_prepare", "archive_inspect", "folder_scan_plan"],
    denied=["network", "subprocess", "filesystem_write", "database_write", "real_clone"],
)
missing_profile = sandbox.decide("missing.profile", "manifest_prepare")
allowed = sandbox.decide("foundation.safe", "manifest_prepare")
not_allowed = sandbox.decide("foundation.safe", "unknown_operation")
explicit_denied = sandbox.decide("foundation.safe", "real_clone")
sensitive_blocked = sandbox.decide("foundation.safe", "folder_scan")
all_ok = sandbox.require_all("foundation.safe", ["manifest_prepare", "archive_inspect"])
all_blocked = sandbox.require_all("foundation.safe", ["manifest_prepare", "real_clone"])

adapters.register_adapter("git.safe.plan", "git", ["manifest_prepare", "real_clone"])
plan = adapters.build_plan("plan.git.safe", "git.safe.plan", "https://example.invalid/repo.git", ["manifest_prepare"])
secured_plan = sandbox.attach_to_plan(plan["plan"], "foundation.safe")
blocked_plan = adapters.build_plan("plan.git.blocked", "git.safe.plan", "https://example.invalid/repo.git", ["real_clone"])
secured_blocked_plan = sandbox.attach_to_plan(blocked_plan["plan"], "foundation.safe")
status = sandbox.status()

print("MARAIM_SANDBOX_ENFORCEMENT_FOUNDATION_SMOKE_OK")
print(status)

assert profile["ok"] is True
assert missing_profile["allowed"] is False
assert allowed["allowed"] is True
assert not_allowed["allowed"] is False
assert explicit_denied["allowed"] is False
assert sensitive_blocked["allowed"] is False
assert all_ok["ok"] is True
assert all_blocked["ok"] is False
assert secured_plan["ok"] is True and secured_plan["plan"]["can_execute"] is True
assert secured_blocked_plan["ok"] is True and secured_blocked_plan["plan"]["can_execute"] is False
assert status["profiles"] == 1
assert status["blocked"] >= 4

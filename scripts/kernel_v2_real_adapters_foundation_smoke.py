import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from maraim.kernel_v2 import KernelV2, RealAdapterFoundation

kernel = KernelV2(dna_root="dna")
adapters = RealAdapterFoundation(kernel)

git = adapters.register_adapter("git.safe.plan", "git", ["manifest_prepare", "dna_extract"])
archive = adapters.register_adapter("archive.safe.plan", "archive", ["manifest_prepare", "archive_inspect"])
folder = adapters.register_adapter("folder.safe.plan", "folder", ["manifest_prepare", "folder_scan_plan"])
invalid = adapters.register_adapter("invalid.safe.plan", "network", ["fetch"])

git_ok = adapters.validate_adapter("git.safe.plan", ["manifest_prepare"])
git_missing = adapters.validate_adapter("git.safe.plan", ["real_clone"])
missing_adapter = adapters.validate_adapter("missing.adapter", ["manifest_prepare"])

git_plan = adapters.build_plan("plan.git.1", "git.safe.plan", "https://example.invalid/repo.git", ["manifest_prepare"])
archive_plan = adapters.build_plan("plan.archive.1", "archive.safe.plan", "sample.zip", ["archive_inspect"])
folder_plan = adapters.build_plan("plan.folder.1", "folder.safe.plan", "./sample", ["folder_scan_plan"])
blocked_plan = adapters.build_plan("plan.git.blocked", "git.safe.plan", "https://example.invalid/repo.git", ["real_clone"])
readiness = adapters.readiness()
status = adapters.status()

print("MARAIM_REAL_ADAPTERS_FOUNDATION_SMOKE_OK")
print(readiness)
print(status)

assert git["ok"] is True
assert archive["ok"] is True
assert folder["ok"] is True
assert invalid["ok"] is False
assert git_ok["ok"] is True
assert git_missing["ok"] is False
assert missing_adapter["ok"] is False
assert git_plan["ok"] is True and git_plan["plan"]["can_execute"] is True
assert archive_plan["plan"]["can_execute"] is True
assert folder_plan["plan"]["can_execute"] is True
assert blocked_plan["plan"]["can_execute"] is False
assert readiness["adapters"] == 3
assert readiness["plans"] == 4
assert readiness["ready"] == 3
assert readiness["blocked"] == 1
assert status["by_type"]["git"] == 1
assert status["by_type"]["archive"] == 1
assert status["by_type"]["folder"] == 1

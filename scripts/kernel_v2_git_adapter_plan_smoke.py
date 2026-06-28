import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from maraim.kernel_v2 import GIT_ADAPTER_PLAN_STEPS, GitAdapterImplementationPlan, KernelV2

kernel = KernelV2(dna_root="dna")
plan = GitAdapterImplementationPlan(kernel)
started = plan.initialize()
outputs = {step: ["code", "test", "audit"] for step in GIT_ADAPTER_PLAN_STEPS}
checked = plan.attach_outputs(outputs)
bad = plan.mark("missing_step", "planned")
report = plan.report()
summary = report["summary"]

print("MARAIM_GIT_ADAPTER_PLAN_SMOKE_OK")
print(summary)

assert started["ok"] is True
assert started["total"] == 20
assert len(GIT_ADAPTER_PLAN_STEPS) == 20
assert checked["ok"] is True
assert bad["ok"] is False
assert report["ok"] is True
assert summary["initialized"] == 20
assert summary["with_outputs"] == 20

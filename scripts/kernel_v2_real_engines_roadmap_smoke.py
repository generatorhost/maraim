import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from maraim.kernel_v2 import KernelV2, REAL_ENGINE_STAGES, RealEnginesRoadmap

kernel = KernelV2(dna_root="dna")
roadmap = RealEnginesRoadmap(kernel)
start = roadmap.initialize()
outputs = {}
for stage in REAL_ENGINE_STAGES:
    outputs[stage] = ["code", "test", "export"]
checked = roadmap.require_outputs(outputs)
bad = roadmap.mark("missing_stage", "planned")
report = roadmap.report()
summary = report["summary"]

print("MARAIM_REAL_ENGINES_ROADMAP_SMOKE_OK")
print(summary)

assert start["ok"] is True
assert start["total"] == 20
assert len(REAL_ENGINE_STAGES) == 20
assert checked["ok"] is True
assert bad["ok"] is False
assert report["ok"] is True
assert summary["initialized"] == 20
assert summary["with_outputs"] == 20

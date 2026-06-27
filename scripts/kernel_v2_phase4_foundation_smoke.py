import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from maraim.kernel_v2 import KernelV2
from maraim.kernel_v2.phase4_foundation import PHASE4_STAGES, Phase4FoundationEngine

kernel = KernelV2(dna_root="dna")
phase4 = Phase4FoundationEngine(kernel)

initialized = phase4.initialize(owner="phase4_smoke")
for stage in PHASE4_STAGES:
    phase4.add_requirement(stage, "preflight")
    phase4.add_requirement(stage, "guard")
    phase4.add_requirement(stage, "smoke")

ready_items = []
for stage in PHASE4_STAGES[:5]:
    ready_items.append(phase4.mark_ready(stage, {"gate": "phase4_smoke"}))

evaluation = phase4.evaluate()
manifest = phase4.manifest("phase4-foundation.25")
missing = phase4.add_requirement("missing.stage", "guard")
status = phase4.status()

print("MARAIM_PHASE4_FOUNDATION_SMOKE_OK")
print(evaluation)
print(status)

assert initialized["ok"] is True
assert initialized["count"] == 25
assert len(PHASE4_STAGES) == 25
assert len(ready_items) == 5
assert all(item["ok"] for item in ready_items)
assert evaluation["total"] == 25
assert evaluation["ready"] == 5
assert evaluation["planned"] == 20
assert evaluation["missing_requirements"] == []
assert manifest["ok"] is True
assert len(manifest["manifest"]["stages"]) == 25
assert missing["ok"] is False
assert status["stages"] == 25
assert status["history"] >= 1 + (25 * 3) + 5 + 1

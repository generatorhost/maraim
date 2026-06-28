import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from maraim.kernel_v2 import KernelV2, PHASE3_STEPS, ProductionBridgePhase3

kernel = KernelV2(dna_root="dna")
phase3 = ProductionBridgePhase3(kernel)
completed = phase3.complete()
invalid = phase3.add("invalid_phase3_step", False)
summary = phase3.summary()

print("MARAIM_PRODUCTION_BRIDGE_PHASE3_SMOKE_OK")
print(summary)

assert completed["ok"] is True
assert len(completed["results"]) == 10
assert len(PHASE3_STEPS) == 10
assert invalid["ok"] is False
assert summary["ok"] is True
assert summary["seen"] == 10
assert summary["percent"] == 100.0

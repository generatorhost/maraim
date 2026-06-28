import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from maraim.kernel_v2 import KernelV2, PHASE2_STEPS, ProductionBridgePhase2

kernel = KernelV2(dna_root="dna")
phase2 = ProductionBridgePhase2(kernel)
completed = phase2.complete()
invalid = phase2.add("invalid_phase2_step", False)
summary = phase2.summary()

print("MARAIM_PRODUCTION_BRIDGE_PHASE2_SMOKE_OK")
print(summary)

assert completed["ok"] is True
assert len(completed["results"]) == 10
assert len(PHASE2_STEPS) == 10
assert invalid["ok"] is False
assert summary["ok"] is True
assert summary["seen"] == 10
assert summary["percent"] == 100.0

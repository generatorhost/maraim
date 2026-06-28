import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from maraim.kernel_v2 import KernelV2, ProductionBridgeSteps

kernel = KernelV2(dna_root="dna")
bridge = ProductionBridgeSteps(kernel)
completed = bridge.complete_default_path("production-bridge-smoke")
invalid = bridge.add("invalid_step", "bad", False)
summary = bridge.summary()

print("MARAIM_PRODUCTION_BRIDGE_STEPS_SMOKE_OK")
print(summary)

assert completed["ok"] is True
assert len(completed["results"]) == 10
assert invalid["ok"] is False
assert summary["complete"] is True
assert summary["percent"] == 100.0
assert summary["seen"] == 10

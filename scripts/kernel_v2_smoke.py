import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from maraim.kernel_v2 import KernelV2

kernel = KernelV2(dna_root="dna")
status = kernel.boot()
text_generation = kernel.resources.resolve_capability("text_generation")
research = kernel.resources.resolve_capability("research")
mission = kernel.resources.resolve_capability("mission_planning")
swarm = kernel.resources.resolve_capability("swarm_spawn")

print("MARAIM_KERNEL_V2_SMOKE_OK")
print(status["state"])
print(status["graph"]["nodes"])
print(text_generation)
print(research)
print(mission)
print(swarm)

assert status["state"] == "running"
assert status["graph"]["nodes"] >= 4
assert text_generation["ok"] is True
assert research["ok"] is True
assert mission["ok"] is True
assert swarm["ok"] is True

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from maraim.kernel_v2 import KernelV2

kernel = KernelV2(dna_root="dna")
status = kernel.boot()
resolution = kernel.resources.resolve_capability("text_generation")

print("MARAIM_KERNEL_V2_SMOKE_OK")
print(status["state"])
print(status["graph"]["nodes"])
print(resolution)

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from maraim.kernel_v2 import KernelV2, RealSourceReadiness

kernel = KernelV2(dna_root="dna")
readiness = RealSourceReadiness(kernel)

git = readiness.add("git-source", "git", ["sandbox", "audit", "recovery"])
archive = readiness.add("archive-source", "archive", ["sandbox", "audit"])
blocked = readiness.add("", "folder", [])
status = readiness.status()

print("MARAIM_REAL_SOURCE_READINESS_SMOKE_OK")
print(status)

assert git["record"]["ready"] is True
assert archive["record"]["ready"] is True
assert blocked["record"]["ready"] is False
assert status["records"] == 3
assert status["ready"] == 2
assert status["blocked"] == 1

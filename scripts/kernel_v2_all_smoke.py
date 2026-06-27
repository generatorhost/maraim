import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CANONICAL_SMOKE_GATE = "scripts/kernel_v2_phase2_plus4_smoke.py"

gate = ROOT / CANONICAL_SMOKE_GATE
if not gate.exists():
    raise FileNotFoundError(CANONICAL_SMOKE_GATE)

runpy.run_path(str(gate), run_name="__main__")

print("MARAIM_KERNEL_V2_ALL_SMOKE_OK")
print({"canonical_gate": CANONICAL_SMOKE_GATE})

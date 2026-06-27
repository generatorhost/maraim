import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "scripts/kernel_v2_all_smoke.py"

print("MARAIM_KERNEL_V2_PHASE2_PLUS4_SMOKE_DEPRECATED")
print({"use": "scripts/kernel_v2_all_smoke.py"})
runpy.run_path(str(CANONICAL), run_name="__main__")

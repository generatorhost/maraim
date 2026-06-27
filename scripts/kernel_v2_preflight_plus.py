import importlib
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

runpy.run_path(str(ROOT / "scripts/kernel_v2_preflight.py"), run_name="__main__")
module = importlib.import_module("maraim.kernel_v2.trace_engine")
print("MARAIM_KERNEL_V2_PREFLIGHT_PLUS_OK")
print({"extra_import": module.__name__})
assert module.__name__ == "maraim.kernel_v2.trace_engine"

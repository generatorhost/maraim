import importlib
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

runpy.run_path(str(ROOT / "scripts/kernel_v2_preflight_plus.py"), run_name="__main__")
for module_name in ["maraim.kernel_v2.report_builder", "maraim.kernel_v2.snapshot_builder"]:
    module = importlib.import_module(module_name)
    print({"extra_import": module.__name__})

print("MARAIM_KERNEL_V2_PREFLIGHT_PLUS2_OK")

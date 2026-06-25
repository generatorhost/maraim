import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from maraim.kernel2 import MaraimKernel

kernel = MaraimKernel()
status = kernel.start()
print("MARAIM_KERNEL2_SMOKE_OK")
print(status)

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from maraim.kernel2 import MaraimKernel

kernel = MaraimKernel()
status = kernel.start()
result = kernel.route_task({"type": "project_analysis", "project_id": 1, "title": "Smoke test project"})
print("MARAIM_KERNEL2_SOCIETY_SMOKE_OK")
print(status["registry_counts"])
print(result)

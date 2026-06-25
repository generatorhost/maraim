import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from maraim.kernel2 import MaraimKernel

kernel = MaraimKernel()
status = kernel.start()
task_result = kernel.route_task({"type": "project_analysis", "project_id": 101, "title": "Task Runtime Smoke"})
workflow_result = kernel.run_workflow("project-acquisition", {"project_id": 101})
print("MARAIM_KERNEL2_TASK_RUNTIME_SMOKE_OK")
print(status["registry_counts"])
print(task_result)
print(workflow_result)
print(kernel.status()["scheduler"])
print(kernel.status()["memory"])

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from maraim.kernel2.app_bridge import kernel_status, route_task, run_workflow, run_mcp_tool

status = kernel_status()
route = route_task({"type": "project_discovery", "title": "Bridge Smoke"})
workflow = run_workflow("project-acquisition", {"title": "Bridge Workflow Smoke"})
mcp = run_mcp_tool("kernel.status", {})

print("MARAIM_KERNEL2_APP_BRIDGE_SMOKE_OK")
print(status["state"])
print(status["registry_counts"])
print(route["ok"])
print(workflow["ok"])
print(mcp["ok"])

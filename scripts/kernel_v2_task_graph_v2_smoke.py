import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from maraim.kernel_v2 import DependencyResolverV2, DNAExtractorEngine, KernelV2, RuntimeStore, TaskGraphV2

kernel = KernelV2(dna_root="dna")
extractor = DNAExtractorEngine(kernel)
store = RuntimeStore(kernel)
resolver = DependencyResolverV2(kernel, store)
task_graph = TaskGraphV2(kernel, resolver)

package = extractor.extract_from_tree(
    "task_graph_sample",
    [
        "plugins/freelance_plugin.py",
        "connectors/source_connector.py",
        "providers/language_provider.py",
        "tools/proposal_tool.py",
    ],
    metadata={"source": "task_graph_smoke"},
    file_contents={
        "plugins/freelance_plugin.py": "def prepare(project):\n    return project\n",
        "connectors/source_connector.py": "def collect(source):\n    return source\n",
        "providers/language_provider.py": "def complete(prompt):\n    return prompt\n",
        "tools/proposal_tool.py": "def draft(project):\n    return project\n",
    },
)

registered = resolver.register_from_package(package)
plugin_id = next(obj["id"] for obj in package["runtime_objects"] if obj["kind"] == "plugin")
connector_id = next(obj["id"] for obj in package["runtime_objects"] if obj["kind"] == "connector")
provider_id = next(obj["id"] for obj in package["runtime_objects"] if obj["kind"] == "provider")
manual_edges = resolver.register_edges([
    {"source": plugin_id, "relation": "plugin_uses_connector", "target": connector_id, "metadata": {}},
    {"source": connector_id, "relation": "connector_uses_provider", "target": provider_id, "metadata": {}},
])

graph = task_graph.build_from_runtime(plugin_id, goal="prepare_freelance_proposal")
ready_initial = task_graph.ready_tasks(graph["id"])
ready_after_provider = task_graph.ready_tasks(graph["id"], completed_runtimes=[provider_id])
plan = task_graph.export_plan(graph["id"])
first_task_id = graph["tasks"][0]["id"]
marked = task_graph.mark_task(graph["id"], first_task_id, "completed")
missing_graph = task_graph.export_plan("missing.graph")
status = task_graph.status()

print("MARAIM_TASK_GRAPH_V2_SMOKE_OK")
print(graph)
print(ready_initial)
print(plan)

assert package["ok"] is True
assert registered["ok"] is True
assert manual_edges["ok"] is True and manual_edges["count"] >= 2
assert graph["id"]
assert graph["tasks"]
assert graph["root"] == plugin_id
assert ready_initial["ok"] is True
assert ready_initial["ready_count"] >= 1
assert ready_after_provider["ok"] is True
assert plan["ok"] is True
assert plan["task_count"] == len(graph["tasks"])
assert marked["ok"] is True
assert marked["task"]["status"] == "completed"
assert missing_graph["ok"] is False
assert status["graphs"] >= 1
assert status["history"] >= 2

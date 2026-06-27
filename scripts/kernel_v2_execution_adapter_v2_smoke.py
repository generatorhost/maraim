import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from maraim.kernel_v2 import (
    DependencyResolverV2,
    DNAExtractorEngine,
    ExecutionAdapterV2,
    KernelV2,
    RuntimeStore,
    TaskGraphV2,
)

kernel = KernelV2(dna_root="dna")
extractor = DNAExtractorEngine(kernel)
store = RuntimeStore(kernel)
resolver = DependencyResolverV2(kernel, store)
task_graph = TaskGraphV2(kernel, resolver)
executor = ExecutionAdapterV2(kernel, task_graph)

package = extractor.extract_from_tree(
    "execution_adapter_sample",
    [
        "plugins/freelance_plugin.py",
        "connectors/source_connector.py",
        "providers/language_provider.py",
    ],
    metadata={"source": "execution_adapter_smoke"},
    file_contents={
        "plugins/freelance_plugin.py": "def prepare(project):\n    return project\n",
        "connectors/source_connector.py": "def collect(source):\n    return source\n",
        "providers/language_provider.py": "def complete(prompt):\n    return prompt\n",
    },
)

resolver.register_from_package(package)
plugin_id = next(obj["id"] for obj in package["runtime_objects"] if obj["kind"] == "plugin")
connector_id = next(obj["id"] for obj in package["runtime_objects"] if obj["kind"] == "connector")
provider_id = next(obj["id"] for obj in package["runtime_objects"] if obj["kind"] == "provider")
resolver.register_edges([
    {"source": plugin_id, "relation": "plugin_uses_connector", "target": connector_id, "metadata": {}},
    {"source": connector_id, "relation": "connector_uses_provider", "target": provider_id, "metadata": {}},
])

graph = task_graph.build_from_runtime(plugin_id, goal="execute_freelance_plan")
dry_run = executor.dry_run(graph["id"])
first_run = executor.run(graph["id"])
resumed = executor.resume(first_run["id"])
missing = executor.resume("missing.run")
status = executor.status()

print("MARAIM_EXECUTION_ADAPTER_V2_SMOKE_OK")
print(dry_run)
print(first_run)
print(status)

assert package["ok"] is True
assert graph["id"]
assert dry_run["ok"] is True
assert dry_run["count"] == len(graph["tasks"])
assert first_run["id"]
assert first_run["results"]
assert first_run["completed_runtimes"]
assert resumed["id"]
assert missing["ok"] is False
assert status["runs"] >= 2
assert status["history"] >= 2

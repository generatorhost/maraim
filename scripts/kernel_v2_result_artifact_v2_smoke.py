import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from maraim.kernel_v2 import (
    DependencyResolverV2,
    DNAExtractorEngine,
    ExecutionAdapterV2,
    KernelV2,
    PermissionSandbox,
    ResultArtifactV2,
    RuntimeStorageEngine,
    RuntimeStore,
    TaskGraphV2,
)

kernel = KernelV2(dna_root="dna")
extractor = DNAExtractorEngine(kernel)
store = RuntimeStore(kernel)
storage = RuntimeStorageEngine(kernel)
resolver = DependencyResolverV2(kernel, store)
task_graph = TaskGraphV2(kernel, resolver)
sandbox = PermissionSandbox(kernel)
executor = ExecutionAdapterV2(kernel, task_graph, sandbox)
artifacts = ResultArtifactV2(kernel, storage)

package = extractor.extract_from_tree(
    "result_artifact_sample",
    [
        "plugins/freelance_plugin.py",
        "connectors/source_connector.py",
        "providers/language_provider.py",
    ],
    metadata={"source": "result_artifact_smoke"},
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

graph = task_graph.build_from_runtime(plugin_id, goal="artifact_capture_plan")
dry_run = executor.dry_run(graph["id"])
for step in dry_run["steps"]:
    sandbox.grant(step["runtime"], ["execute_simulated"], reason="result_artifact_smoke")
run_result = executor.run(graph["id"])
captured = artifacts.capture_run(run_result, label="smoke_result")
artifact_id = captured["artifact"]["id"]
loaded = artifacts.get(artifact_id)
listed = artifacts.list()
summary = artifacts.summarize(artifact_id)
missing = artifacts.summarize("missing.artifact")
status = artifacts.status()

print("MARAIM_RESULT_ARTIFACT_V2_SMOKE_OK")
print(summary)
print(status)

assert package["ok"] is True
assert run_result["id"]
assert captured["ok"] is True
assert captured["artifact"]["permission_summary"]["allowed"] >= 1
assert loaded["ok"] is True
assert listed["count"] >= 1
assert summary["ok"] is True
assert summary["artifact"] == artifact_id
assert summary["result_count"] == len(run_result["results"])
assert summary["permission_summary"]["allowed"] >= 1
assert summary["permission_summary"]["blocked"] == 0
assert missing["ok"] is False
assert status["artifacts"] >= 1
assert status["storage"]["items"] >= 1

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
    RuntimeAuditTrail,
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
audit = RuntimeAuditTrail(kernel)

package = extractor.extract_from_tree(
    "audit_trail_sample",
    [
        "plugins/freelance_plugin.py",
        "connectors/source_connector.py",
        "providers/language_provider.py",
    ],
    metadata={"source": "audit_trail_smoke"},
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

graph = task_graph.build_from_runtime(plugin_id, goal="audit_runtime_plan")
dry_run = executor.dry_run(graph["id"])
for step in dry_run["steps"]:
    sandbox.grant(step["runtime"], ["execute_simulated"], reason="audit_trail_smoke")
run_result = executor.run(graph["id"])
captured = artifacts.capture_run(run_result, label="audit_result")
audit_run = audit.capture_run(run_result)
audit_artifact = audit.capture_artifact(captured)
manual = audit.record("manual", "phase2", "checkpoint", "ok", {"note": "audit smoke"})
execution_events = audit.query(event_type="execution")
task_events = audit.query(event_type="execution_task")
artifact_events = audit.query(event_type="artifact")
status = audit.status()

print("MARAIM_AUDIT_TRAIL_SMOKE_OK")
print(status)

assert package["ok"] is True
assert run_result["id"]
assert captured["ok"] is True
assert audit_run["ok"] is True
assert audit_run["count"] >= 1
assert audit_artifact["ok"] is True
assert manual["ok"] is True
assert execution_events["count"] >= 1
assert task_events["count"] >= 1
assert artifact_events["count"] >= 1
assert status["events"] >= 4
assert status["by_type"]["execution"] >= 1
assert status["by_type"]["artifact"] >= 1

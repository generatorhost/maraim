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
    RuntimeMetricsEngine,
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
metrics = RuntimeMetricsEngine(kernel)

package = extractor.extract_from_tree(
    "metrics_engine_sample",
    [
        "plugins/freelance_plugin.py",
        "connectors/source_connector.py",
        "providers/language_provider.py",
    ],
    metadata={"source": "metrics_engine_smoke"},
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

graph = task_graph.build_from_runtime(plugin_id, goal="metrics_runtime_plan")
dry_run = executor.dry_run(graph["id"])
for step in dry_run["steps"]:
    sandbox.grant(step["runtime"], ["execute_simulated"], reason="metrics_engine_smoke")
run_result = executor.run(graph["id"])
captured = artifacts.capture_run(run_result, label="metrics_result")
audit.capture_run(run_result)
audit.capture_artifact(captured)
metric_counter = metrics.increment("smoke.counter", 2, {"suite": "metrics"})
metric_gauge = metrics.gauge("smoke.gauge", 3, {"suite": "metrics"})
metric_timing = metrics.timing("smoke.timing", 1.5, {"suite": "metrics"})
run_metrics = metrics.capture_run(run_result)
audit_metrics = metrics.capture_audit(audit.status())
snapshot = metrics.snapshot()
status = metrics.status()

print("MARAIM_METRICS_ENGINE_SMOKE_OK")
print(snapshot)
print(status)

assert package["ok"] is True
assert run_result["id"]
assert captured["ok"] is True
assert metric_counter["ok"] is True
assert metric_gauge["ok"] is True
assert metric_timing["ok"] is True
assert run_metrics["ok"] is True and run_metrics["count"] >= 4
assert audit_metrics["ok"] is True and audit_metrics["count"] >= 1
assert snapshot["ok"] is True
assert snapshot["counters"]
assert snapshot["gauges"]
assert snapshot["timings"]
assert status["events"] >= 6

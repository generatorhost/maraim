import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from maraim.kernel_v2 import DependencyResolverV2, DNAExtractorEngine, KernelV2, RuntimeStore

kernel = KernelV2(dna_root="dna")
extractor = DNAExtractorEngine(kernel)
store = RuntimeStore(kernel)
resolver = DependencyResolverV2(kernel, store)

package = extractor.extract_from_tree(
    "dependency_resolver_sample",
    [
        "agents/research_agent.py",
        "plugins/freelance_plugin.py",
        "connectors/source_connector.py",
        "providers/language_provider.py",
        "tools/proposal_tool.py",
        "models/sample.gguf",
        "knowledge/guide.md",
    ],
    metadata={"source": "dependency_resolver_smoke"},
    file_contents={
        "agents/research_agent.py": "class ResearchAgent:\n    pass\n",
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
    {"source": plugin_id, "relation": "depends_on", "target": "missing.runtime@1.0.0", "metadata": {}},
])
resolved = resolver.resolve(plugin_id)
explain_plugin = resolver.explain(plugin_id)
explain_provider = resolver.explain(provider_id)
cycle_edges = resolver.register_edges([
    {"source": provider_id, "relation": "depends_on", "target": plugin_id, "metadata": {}},
])
cycle_resolved = resolver.resolve(plugin_id)
status = resolver.status()

print("MARAIM_DEPENDENCY_RESOLVER_V2_SMOKE_OK")
print(resolved)
print(cycle_resolved)
print(status)

assert package["ok"] is True
assert registered["ok"] is True
assert registered["stored"]["ok"] is True
assert registered["edges"]["ok"] is True
assert manual_edges["ok"] is True and manual_edges["count"] >= 3
assert resolved["root"] == plugin_id
assert resolved["nodes"] >= 4
assert "missing.runtime@1.0.0" in resolved["missing"]
assert resolved["order"]
assert explain_plugin["ok"] is True and explain_plugin["outgoing"]
assert explain_provider["ok"] is True and explain_provider["incoming"]
assert cycle_edges["ok"] is True and cycle_edges["count"] >= 1
assert cycle_resolved["cycles"]
assert status["edges"] >= manual_edges["count"]
assert status["runs"] >= 2

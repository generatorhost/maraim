import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from maraim.kernel_v2 import (
    ConnectorRuntimeEngine,
    DNAExtractorEngine,
    KernelV2,
    PluginRuntimeEngine,
    ProviderEngine,
    ToolRuntimeEngine,
)

kernel = KernelV2(dna_root="dna")
extractor = DNAExtractorEngine(kernel)

package = extractor.extract_from_tree(
    "runtime_systems_sample",
    [
        "plugins/freelance_plugin.py",
        "connectors/source_connector.py",
        "integrations/message_integration.py",
        "providers/language_provider.py",
        "tools/proposal_tool.py",
    ],
    metadata={"source": "runtime_systems_smoke"},
    file_contents={
        "plugins/freelance_plugin.py": "def prepare(project):\n    return project\n",
        "connectors/source_connector.py": "def collect(source):\n    return source\n",
        "integrations/message_integration.py": "def notify(target, text):\n    return True\n",
        "providers/language_provider.py": "def complete(prompt):\n    return prompt\n",
        "tools/proposal_tool.py": "def draft(project):\n    return project\n",
    },
)

plugin_engine = PluginRuntimeEngine(kernel)
connector_engine = ConnectorRuntimeEngine(kernel)
provider_engine = ProviderEngine(kernel)
tool_engine = ToolRuntimeEngine(kernel)

plugin_register = plugin_engine.register_from_runtime_objects(package["runtime_objects"])
connector_register = connector_engine.register_from_runtime_objects(package["runtime_objects"])
provider_register = provider_engine.register_from_runtime_objects(package["runtime_objects"])
tool_register = tool_engine.register_from_runtime_objects(package["runtime_objects"])

plugin_id = plugin_register["registered"][0] if plugin_register["registered"] else plugin_register["reused"][0]
connector_id = connector_register["registered"][0] if connector_register["registered"] else connector_register["reused"][0]
provider_id = provider_register["registered"][0] if provider_register["registered"] else provider_register["reused"][0]
tool_id = tool_register["registered"][0] if tool_register["registered"] else tool_register["reused"][0]

plugin_bind = plugin_engine.bind(plugin_id, connector_id, relation="plugin_uses_connector")
connector_bind = connector_engine.bind(connector_id, provider_id, relation="connector_uses_provider")
tool_bind = tool_engine.bind(tool_id, provider_id, relation="tool_uses_provider")

plugin_invoke = plugin_engine.invoke(plugin_id, action="prepare", payload={"project": "sample"})
connector_invoke = connector_engine.invoke(connector_id, action="collect", payload={"source": "sample"})
provider_invoke = provider_engine.invoke(provider_id, action="complete", payload={"prompt": "sample"})
tool_invoke = tool_engine.invoke(tool_id, action="draft", payload={"project": "sample"})

print("MARAIM_RUNTIME_SYSTEMS_SMOKE_OK")
print(plugin_engine.status())
print(connector_engine.status())
print(provider_engine.status())
print(tool_engine.status())

assert package["ok"] is True
assert {"plugin", "connector", "integration", "provider", "tool"}.issubset({obj["kind"] for obj in package["runtime_objects"]})
assert plugin_register["ok"] is True and plugin_register["count"] >= 1
assert connector_register["ok"] is True and connector_register["count"] >= 2
assert provider_register["ok"] is True and provider_register["count"] >= 1
assert tool_register["ok"] is True and tool_register["count"] >= 1
assert plugin_bind["ok"] is True
assert connector_bind["ok"] is True
assert tool_bind["ok"] is True
assert plugin_invoke["ok"] is True
assert connector_invoke["ok"] is True
assert provider_invoke["ok"] is True
assert tool_invoke["ok"] is True
assert plugin_engine.status()["runtimes"] >= 1
assert connector_engine.status()["runtimes"] >= 2
assert provider_engine.status()["runtimes"] >= 1
assert tool_engine.status()["runtimes"] >= 1

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from maraim.kernel_v2 import DNAExtractorEngine, KernelV2, RuntimeStore

kernel = KernelV2(dna_root="dna")
extractor = DNAExtractorEngine(kernel)
store = RuntimeStore(kernel)

package = extractor.extract_from_tree(
    "runtime_store_sample",
    [
        "agents/research_agent.py",
        "plugins/freelance_plugin.py",
        "connectors/source_connector.py",
        "providers/language_provider.py",
        "tools/proposal_tool.py",
        "models/sample.gguf",
        "knowledge/guide.md",
        "database/schema.sql",
    ],
    metadata={"source": "runtime_store_smoke"},
    file_contents={
        "agents/research_agent.py": "class ResearchAgent:\n    pass\ndef analyze():\n    return True\n",
        "plugins/freelance_plugin.py": "def prepare(project):\n    return project\n",
        "connectors/source_connector.py": "def collect(source):\n    return source\n",
        "providers/language_provider.py": "def complete(prompt):\n    return prompt\n",
        "tools/proposal_tool.py": "def draft(project):\n    return project\n",
    },
)

register = store.register_from_specs(package["runtime_objects"], source="extracted_smoke")
status_after_register = store.status()
agent_list = store.list(kind="agent")
plugin_list = store.list(kind="plugin")
tool_list = store.list(capability="tool_execution")
plugin_id = plugin_list["records"][0]["id"]
plugin_get = store.get(plugin_id)
plugin_snapshot = store.snapshot(plugin_id, label="before_disable")
plugin_disable = store.disable(plugin_id, reason="smoke_disable")
disabled_list = store.list(enabled=False)
plugin_restore = store.restore(plugin_id)
plugin_enable = store.enable(plugin_id, reason="smoke_enable")
plugin_unmount = store.mark_unmounted(plugin_id, reason="smoke_unmount")
unmounted_list = store.list(mounted=False)
plugin_mount = store.mark_mounted(plugin_id, reason="smoke_mount")
missing = store.get("missing.runtime@1.0.0")
status_final = store.status()

print("MARAIM_RUNTIME_STORE_SMOKE_OK")
print(status_after_register)
print(status_final)

assert package["ok"] is True
assert register["ok"] is True
assert register["count"] >= len(package["runtime_objects"])
assert status_after_register["runtimes"] >= len(package["runtime_objects"])
assert status_after_register["by_source"]["extracted_smoke"] >= len(package["runtime_objects"])
assert agent_list["count"] >= 1
assert plugin_list["count"] >= 1
assert tool_list["count"] >= 1
assert plugin_get["ok"] is True
assert plugin_snapshot["ok"] is True
assert plugin_disable["ok"] is True
assert disabled_list["count"] >= 1
assert plugin_restore["ok"] is True
assert plugin_enable["ok"] is True
assert plugin_unmount["ok"] is True
assert unmounted_list["count"] >= 1
assert plugin_mount["ok"] is True
assert missing["ok"] is False
assert status_final["snapshots"] >= 1
assert status_final["history"] >= 7
assert status_final["enabled"] == status_final["runtimes"]
assert status_final["mounted"] >= 1

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from maraim.kernel_v2 import DNAExtractorEngine, KernelV2, RuntimeMountManager, RuntimeStore

kernel = KernelV2(dna_root="dna")
extractor = DNAExtractorEngine(kernel)
store = RuntimeStore(kernel)
mounts = RuntimeMountManager(kernel, store)

package = extractor.extract_from_tree(
    "mount_manager_sample",
    [
        "agents/research_agent.py",
        "plugins/freelance_plugin.py",
        "connectors/source_connector.py",
        "tools/proposal_tool.py",
    ],
    metadata={"source": "mount_manager_smoke"},
    file_contents={
        "agents/research_agent.py": "class ResearchAgent:\n    pass\n",
        "plugins/freelance_plugin.py": "def prepare(project):\n    return project\n",
        "connectors/source_connector.py": "def collect(source):\n    return source\n",
        "tools/proposal_tool.py": "def draft(project):\n    return project\n",
    },
)

register = store.register_from_specs(package["runtime_objects"], source="mount_smoke")
plugin = store.list(kind="plugin")["records"][0]
plugin_id = plugin["id"]

unmount_one = mounts.unmount(plugin_id, reason="smoke_unmount_one")
mount_one = mounts.mount(plugin_id, reason="smoke_mount_one")
remount_one = mounts.remount(plugin_id, reason="smoke_remount_one")
unmount_tools = mounts.unmount_by_capability("tool_execution", reason="smoke_unmount_tools")
mount_tools = mounts.mount_by_capability("tool_execution", reason="smoke_mount_tools")
unmount_plugins = mounts.unmount_by_kind("plugin", reason="smoke_unmount_plugins")
mount_plugins = mounts.mount_by_kind("plugin", reason="smoke_mount_plugins")
missing = mounts.mount("missing.runtime@1.0.0")
status = mounts.status()

print("MARAIM_MOUNT_MANAGER_SMOKE_OK")
print(status)

assert package["ok"] is True
assert register["ok"] is True
assert unmount_one["ok"] is True
assert mount_one["ok"] is True
assert remount_one["ok"] is True
assert unmount_tools["ok"] is True and unmount_tools["count"] >= 1
assert mount_tools["ok"] is True and mount_tools["count"] >= 1
assert unmount_plugins["ok"] is True and unmount_plugins["count"] >= 1
assert mount_plugins["ok"] is True and mount_plugins["count"] >= 1
assert missing["ok"] is False
assert status["operations"] >= 7
assert status["runtimes"] >= 4
assert status["mounted"] >= 1

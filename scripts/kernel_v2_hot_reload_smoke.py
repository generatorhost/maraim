import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from maraim.kernel_v2 import DNAExtractorEngine, HotReloadEngine, KernelV2, RuntimeStore

kernel = KernelV2(dna_root="dna")
extractor = DNAExtractorEngine(kernel)
store = RuntimeStore(kernel)
hot_reload = HotReloadEngine(kernel, store)

initial = extractor.extract_from_tree(
    "hot_reload_initial",
    [
        "plugins/freelance_plugin.py",
        "connectors/source_connector.py",
        "tools/proposal_tool.py",
    ],
    metadata={"source": "hot_reload_initial"},
    file_contents={
        "plugins/freelance_plugin.py": "def prepare(project):\n    return project\n",
        "connectors/source_connector.py": "def collect(source):\n    return source\n",
        "tools/proposal_tool.py": "def draft(project):\n    return project\n",
    },
)

initial_apply = hot_reload.apply_reload(initial["runtime_objects"], source="initial_load")
initial_status = hot_reload.status()

changed = extractor.extract_from_tree(
    "hot_reload_changed",
    [
        "plugins/freelance_plugin.py",
        "providers/language_provider.py",
        "tools/proposal_tool.py",
    ],
    metadata={"source": "hot_reload_changed"},
    file_contents={
        "plugins/freelance_plugin.py": "def prepare(project):\n    return {'proposal': project}\n",
        "providers/language_provider.py": "def complete(prompt):\n    return prompt\n",
        "tools/proposal_tool.py": "def draft(project):\n    return {'draft': project}\n",
    },
)

changed_plan = hot_reload.plan_reload(changed["runtime_objects"])
changed_apply = hot_reload.apply_reload(changed["runtime_objects"], source="changed_load", remove_missing=False)
final_status = hot_reload.status()
store_status = store.status()
plugin_records = store.list(kind="plugin")
provider_records = store.list(kind="provider")
unmounted_records = store.list(mounted=False)

print("MARAIM_HOT_RELOAD_SMOKE_OK")
print(initial_status)
print(changed_plan)
print(final_status)

assert initial["ok"] is True
assert changed["ok"] is True
assert initial_apply["ok"] is True
assert initial_apply["plan"]["created"]
assert initial_status["reloads"] == 1
assert changed_plan["ok"] is True
assert changed_plan["created"]
assert changed_plan["updated"]
assert changed_plan["removed"]
assert changed_apply["ok"] is True
assert changed_apply["snapshots"]
assert changed_apply["stored"]
assert changed_apply["removed"]
assert final_status["reloads"] == 2
assert store_status["runtimes"] >= 4
assert store_status["snapshots"] >= 1
assert plugin_records["count"] >= 1
assert provider_records["count"] >= 1
assert unmounted_records["count"] >= 1

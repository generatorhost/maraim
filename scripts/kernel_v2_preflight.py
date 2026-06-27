import compileall
import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

MODULES = [
    "maraim.kernel_v2.runtime_object",
    "maraim.kernel_v2.runtime_graph",
    "maraim.kernel_v2.dna_manager",
    "maraim.kernel_v2.dna_extractor_engine",
    "maraim.kernel_v2.dna_package_engine",
    "maraim.kernel_v2.model_engine",
    "maraim.kernel_v2.runtime_systems",
    "maraim.kernel_v2.runtime_store",
    "maraim.kernel_v2.hot_reload",
    "maraim.kernel_v2.mount_manager",
    "maraim.kernel_v2.storage_engine",
    "maraim.kernel_v2.health_engine",
    "maraim.kernel_v2.source_adapters",
    "maraim.kernel_v2.dependency_resolver_v2",
    "maraim.kernel_v2.task_graph_v2",
    "maraim.kernel_v2.execution_adapter_v2",
    "maraim.kernel_v2.result_artifact_v2",
    "maraim.kernel_v2.permission_sandbox",
    "maraim.kernel_v2.audit_trail",
    "maraim.kernel_v2",
]

compile_ok = compileall.compile_dir(str(ROOT / "maraim"), quiet=1)
imports = []
for module_name in MODULES:
    module = importlib.import_module(module_name)
    imports.append(module.__name__)

print("MARAIM_KERNEL_V2_PREFLIGHT_OK")
print({"compiled": compile_ok, "imports": imports})

assert compile_ok is True
assert len(imports) == len(MODULES)

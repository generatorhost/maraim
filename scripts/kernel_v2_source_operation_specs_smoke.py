import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from maraim.kernel_v2 import KernelV2
from maraim.kernel_v2.source_ops import SourceOperationSpecs

kernel = KernelV2(dna_root="dna")
specs = SourceOperationSpecs(kernel)
imported = specs.add("import_source", "repo-alpha", "workspace-alpha", {"kind": "git"})
refreshed = specs.add("refresh_source", "repo-alpha", "workspace-alpha", {})
selected = specs.add("select_ref", "repo-alpha", "workspace-alpha", {"ref": "main"})
invalid_kind = specs.add("bad_kind", "repo-alpha", "workspace-alpha", {})
unsafe_target = specs.add("import_source", "repo-alpha", "../escape", {})
status = specs.status()

print("MARAIM_SOURCE_OPERATION_SPECS_SMOKE_OK")
print(status)

assert imported["ok"] is True
assert refreshed["ok"] is True
assert selected["ok"] is True
assert invalid_kind["ok"] is False
assert unsafe_target["ok"] is False
assert status["ok"] is True
assert status["specs"] == 3

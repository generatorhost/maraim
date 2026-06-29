import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from maraim.kernel_v2 import KernelV2
from maraim.kernel_v2.source_ops import SourceOperationSpecs
from maraim.kernel_v2.source_spec_validator import SourceSpecValidator

kernel = KernelV2(dna_root="dna")
specs = SourceOperationSpecs(kernel)
validator = SourceSpecValidator(kernel)
valid_spec = specs.add("import_source", "repo-alpha", "workspace-alpha", {})["spec"]
valid = validator.validate(valid_spec)
invalid_mode = validator.validate({"kind": "import_source", "source": "repo", "target": "workspace"})
invalid_kind = validator.validate({"kind": "bad", "source": "repo", "target": "workspace", "mode": "review_only"})
missing = validator.validate({"kind": "import_source", "source": "repo", "mode": "review_only"})
status = validator.status()

print("MARAIM_SOURCE_SPEC_VALIDATOR_SMOKE_OK")
print(status)

assert valid["valid"] is True
assert invalid_mode["valid"] is False
assert invalid_kind["valid"] is False
assert missing["valid"] is False
assert status["checks"] == 4
assert status["valid"] == 1
assert status["invalid"] == 3

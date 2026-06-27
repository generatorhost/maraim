import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from maraim.kernel_v2 import (
    AdapterContractRegistry,
    EvolutionExportPlanner,
    FederationManifestBuilder,
    KernelV2,
    PromotionPlanner,
    ReadinessGate,
    ReleaseManifestBuilder,
    SandboxContractRegistry,
)

kernel = KernelV2(dna_root="dna")
adapters = AdapterContractRegistry(kernel)
sandbox = SandboxContractRegistry(kernel)
readiness = ReadinessGate(kernel)
release = ReleaseManifestBuilder(kernel)
promotion = PromotionPlanner(kernel)
federation = FederationManifestBuilder(kernel)
evolution = EvolutionExportPlanner(kernel)

adapter = adapters.register("git_manifest_adapter", "source", ["manifest_prepare", "dna_extract"], "foundation")
adapter_ok = adapters.validate("git_manifest_adapter", ["manifest_prepare"])
adapter_missing = adapters.validate("git_manifest_adapter", ["real_clone"])

sandbox_contract = sandbox.define("simulated_execution", ["execute_simulated", "read_runtime_store"], ["network_access", "process_spawn"])
sandbox_ok = sandbox.plan("simulated_execution", ["execute_simulated"])
sandbox_blocked = sandbox.plan("simulated_execution", ["process_spawn"])

readiness.add_check("preflight", True, {"gate": "plus2"})
readiness.add_check("guard", True, {"gate": "plus2"})
readiness.add_check("smoke", True, {"gate": "plus2"})
ready = readiness.evaluate()

manifest = release.build("phase3-foundation.1", ["adapter_contracts", "sandbox_contracts", "readiness_gate"], ready)
promo = promotion.plan("phase3_foundation_promotion", "foundation", "adapter_production_candidate", ["preflight", "guard", "smoke"])
fed = federation.build("maraim.local.foundation", ["node.local"], ["manifest_exchange", "capability_listing"])
export_plan = evolution.plan("evolved_dna_export_plan_1", "dna.local.foundation", "mdp", True)

print("MARAIM_PHASE3_FOUNDATION_SMOKE_OK")
print(ready)
print(manifest)

assert adapter["ok"] is True
assert adapter_ok["ok"] is True
assert adapter_missing["ok"] is False
assert sandbox_contract["ok"] is True
assert sandbox_ok["ok"] is True
assert sandbox_blocked["ok"] is False
assert ready["ok"] is True and ready["checks"] == 3
assert manifest["ok"] is True
assert promo["ok"] is True
assert fed["ok"] is True
assert export_plan["ok"] is True
assert adapters.status()["contracts"] == 1
assert sandbox.status()["contracts"] == 1
assert release.status()["manifests"] == 1
assert promotion.status()["plans"] == 1
assert federation.status()["manifests"] == 1
assert evolution.status()["exports"] == 1

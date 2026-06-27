import time
from typing import Any, Dict, Iterable, List, Optional


class AdapterContractRegistry:
    def __init__(self, kernel: Any = None):
        self.kernel = kernel
        self.contracts: Dict[str, Dict[str, Any]] = {}

    def register(self, name: str, adapter_type: str, capabilities: Iterable[str], mode: str = "foundation") -> Dict[str, Any]:
        contract = {"name": name, "adapter_type": adapter_type, "capabilities": list(capabilities), "mode": mode, "created_at": time.time()}
        self.contracts[name] = contract
        return {"ok": True, "contract": contract}

    def validate(self, name: str, required: Iterable[str]) -> Dict[str, Any]:
        contract = self.contracts.get(name)
        if contract is None:
            return {"ok": False, "error": "contract_not_found", "name": name}
        missing = [item for item in required if item not in contract["capabilities"]]
        return {"ok": not missing, "name": name, "missing": missing, "contract": contract}

    def status(self) -> Dict[str, Any]:
        return {"contracts": len(self.contracts), "names": sorted(self.contracts)}


class SandboxContractRegistry:
    def __init__(self, kernel: Any = None):
        self.kernel = kernel
        self.contracts: Dict[str, Dict[str, Any]] = {}

    def define(self, name: str, allowed_permissions: Iterable[str], denied_permissions: Iterable[str]) -> Dict[str, Any]:
        contract = {"name": name, "allowed": sorted(set(allowed_permissions)), "denied": sorted(set(denied_permissions)), "created_at": time.time()}
        self.contracts[name] = contract
        return {"ok": True, "contract": contract}

    def plan(self, name: str, requested: Iterable[str]) -> Dict[str, Any]:
        contract = self.contracts.get(name)
        if contract is None:
            return {"ok": False, "error": "contract_not_found", "name": name}
        denied = [item for item in requested if item in contract["denied"]]
        missing = [item for item in requested if item not in contract["allowed"]]
        return {"ok": not denied and not missing, "name": name, "denied": denied, "missing": missing, "contract": contract}

    def status(self) -> Dict[str, Any]:
        return {"contracts": len(self.contracts), "names": sorted(self.contracts)}


class ReadinessGate:
    def __init__(self, kernel: Any = None):
        self.kernel = kernel
        self.checks: List[Dict[str, Any]] = []

    def add_check(self, name: str, ok: bool, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        check = {"name": name, "ok": bool(ok), "details": details or {}, "created_at": time.time()}
        self.checks.append(check)
        return {"ok": True, "check": check}

    def evaluate(self) -> Dict[str, Any]:
        failed = [item for item in self.checks if not item["ok"]]
        return {"ok": not failed, "checks": len(self.checks), "failed": failed}

    def status(self) -> Dict[str, Any]:
        return self.evaluate()


class ReleaseManifestBuilder:
    def __init__(self, kernel: Any = None):
        self.kernel = kernel
        self.manifests: Dict[str, Dict[str, Any]] = {}

    def build(self, version: str, components: Iterable[str], checks: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        manifest = {"version": version, "components": list(components), "checks": checks or {}, "created_at": time.time()}
        self.manifests[version] = manifest
        return {"ok": True, "manifest": manifest}

    def status(self) -> Dict[str, Any]:
        return {"manifests": len(self.manifests), "versions": sorted(self.manifests)}


class PromotionPlanner:
    def __init__(self, kernel: Any = None):
        self.kernel = kernel
        self.plans: Dict[str, Dict[str, Any]] = {}

    def plan(self, name: str, from_stage: str, to_stage: str, gates: Iterable[str]) -> Dict[str, Any]:
        item = {"name": name, "from": from_stage, "to": to_stage, "gates": list(gates), "created_at": time.time()}
        self.plans[name] = item
        return {"ok": True, "plan": item}

    def status(self) -> Dict[str, Any]:
        return {"plans": len(self.plans), "names": sorted(self.plans)}


class FederationManifestBuilder:
    def __init__(self, kernel: Any = None):
        self.kernel = kernel
        self.manifests: Dict[str, Dict[str, Any]] = {}

    def build(self, federation_id: str, nodes: Iterable[str], capabilities: Iterable[str]) -> Dict[str, Any]:
        manifest = {"federation_id": federation_id, "nodes": list(nodes), "capabilities": list(capabilities), "mode": "manifest_only", "created_at": time.time()}
        self.manifests[federation_id] = manifest
        return {"ok": True, "manifest": manifest}

    def status(self) -> Dict[str, Any]:
        return {"manifests": len(self.manifests), "federations": sorted(self.manifests)}


class EvolutionExportPlanner:
    def __init__(self, kernel: Any = None):
        self.kernel = kernel
        self.exports: Dict[str, Dict[str, Any]] = {}

    def plan(self, export_id: str, source_dna: str, target_format: str, include_history: bool = True) -> Dict[str, Any]:
        item = {"export_id": export_id, "source_dna": source_dna, "target_format": target_format, "include_history": include_history, "mode": "plan_only", "created_at": time.time()}
        self.exports[export_id] = item
        return {"ok": True, "export": item}

    def status(self) -> Dict[str, Any]:
        return {"exports": len(self.exports), "ids": sorted(self.exports)}

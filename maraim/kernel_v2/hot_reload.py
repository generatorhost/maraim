import hashlib
import time
from typing import Any, Dict, Iterable, List, Optional

from .runtime_store import RuntimeStore


class HotReloadEngine:
    """Hot reload foundation built on RuntimeStore.

    This phase does not reload Python modules or mutate files. It computes stable
    fingerprints for extracted runtime specs, detects created/updated/removed
    runtime IDs, snapshots existing records before replacement, and updates
    RuntimeStore mount state. Real module reload, dependency migration, and
    lifecycle-safe remount can be added later on top of this contract.
    """

    def __init__(self, kernel: Any, store: Optional[RuntimeStore] = None):
        self.kernel = kernel
        self.store = store or RuntimeStore(kernel)
        self.reloads: List[Dict[str, Any]] = []

    def fingerprint_specs(self, specs: Iterable[Dict[str, Any]]) -> Dict[str, str]:
        fingerprints: Dict[str, str] = {}
        for spec in specs:
            runtime_id = spec.get("id")
            if not runtime_id:
                continue
            fingerprints[runtime_id] = self._fingerprint_spec(spec)
        return fingerprints

    def plan_reload(self, specs: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
        incoming_specs = list(specs)
        incoming = self.fingerprint_specs(incoming_specs)
        existing = {runtime_id: record for runtime_id, record in self.store.records.items()}
        created = [runtime_id for runtime_id in incoming if runtime_id not in existing]
        removed = [runtime_id for runtime_id in existing if runtime_id not in incoming]
        updated = []
        unchanged = []
        for runtime_id, fingerprint in incoming.items():
            if runtime_id not in existing:
                continue
            previous = existing[runtime_id].get("fingerprint") or existing[runtime_id].get("metadata", {}).get("fingerprint")
            if previous == fingerprint:
                unchanged.append(runtime_id)
            else:
                updated.append(runtime_id)
        return {
            "ok": True,
            "created": created,
            "updated": updated,
            "removed": removed,
            "unchanged": unchanged,
            "incoming": len(incoming),
            "existing": len(existing),
        }

    def apply_reload(
        self,
        specs: Iterable[Dict[str, Any]],
        source: str = "hot_reload",
        remove_missing: bool = False,
        remount: bool = True,
    ) -> Dict[str, Any]:
        incoming_specs = list(specs)
        plan = self.plan_reload(incoming_specs)
        spec_by_id = {spec.get("id"): spec for spec in incoming_specs if spec.get("id")}
        snapshots: List[str] = []
        stored: List[str] = []
        removed: List[str] = []
        mounted: List[str] = []

        for runtime_id in plan["updated"]:
            snap = self.store.snapshot(runtime_id, label="before_hot_reload")
            if snap.get("ok"):
                snapshots.append(runtime_id)

        for runtime_id in plan["created"] + plan["updated"]:
            spec = dict(spec_by_id[runtime_id])
            fingerprint = self._fingerprint_spec(spec)
            metadata = dict(spec.get("metadata", {}))
            metadata["fingerprint"] = fingerprint
            metadata["hot_reload_source"] = source
            spec["metadata"] = metadata
            result = self.store.register_from_specs([spec], source=source)
            if result.get("ok"):
                stored.extend(result.get("stored", []))
            if remount:
                mount = self.store.mark_mounted(runtime_id, mounted=True, reason="hot_reload")
                if mount.get("ok"):
                    mounted.append(runtime_id)

        if remove_missing:
            for runtime_id in plan["removed"]:
                result = self.store.remove(runtime_id, reason="hot_reload_removed")
                if result.get("ok"):
                    removed.append(runtime_id)
        else:
            for runtime_id in plan["removed"]:
                result = self.store.mark_unmounted(runtime_id, reason="hot_reload_missing")
                if result.get("ok"):
                    removed.append(runtime_id)

        reload_record = {
            "ok": True,
            "plan": plan,
            "snapshots": snapshots,
            "stored": stored,
            "removed": removed,
            "mounted": mounted,
            "created_at": time.time(),
        }
        self.reloads.append(reload_record)
        if hasattr(self.kernel, "emit"):
            self.kernel.emit("hot_reload.applied", reload_record)
        return reload_record

    def status(self) -> Dict[str, Any]:
        last = self.reloads[-1] if self.reloads else None
        return {
            "reloads": len(self.reloads),
            "last": last,
            "store": self.store.status(),
        }

    def _fingerprint_spec(self, spec: Dict[str, Any]) -> str:
        digest = hashlib.sha256()
        for key in ["id", "kind", "source_path"]:
            digest.update(str(spec.get(key, "")).encode("utf-8"))
            digest.update(b"\n")
        for capability in sorted(spec.get("capabilities", [])):
            digest.update(str(capability).encode("utf-8"))
            digest.update(b"\n")
        metadata = spec.get("metadata", {}) or {}
        for key in sorted(metadata):
            digest.update(str(key).encode("utf-8"))
            digest.update(b"=")
            digest.update(str(metadata[key]).encode("utf-8"))
            digest.update(b"\n")
        return digest.hexdigest()

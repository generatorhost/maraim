import time
from typing import Any, Dict, List


class SourceOperationSpecs:
    """Review-only source operation specifications."""

    allowed_kinds = {"import_source", "refresh_source", "select_ref"}

    def __init__(self, kernel: Any = None):
        self.kernel = kernel
        self.items: List[Dict[str, Any]] = []

    def add(self, kind: str, source: str, target: str, metadata: Dict[str, Any] | None = None) -> Dict[str, Any]:
        if kind not in self.allowed_kinds:
            return {"ok": False, "error": "kind_not_allowed", "kind": kind}
        validation = self._validate(source, target)
        if not validation["ok"]:
            return validation
        item = {"kind": kind, "source": source, "target": target, "metadata": metadata or {}, "mode": "review_only", "created_at": time.time()}
        self.items.append(item)
        if self.kernel is not None and hasattr(self.kernel, "emit"):
            self.kernel.emit("source_operation_specs.added", item)
        return {"ok": True, "spec": item}

    def status(self) -> Dict[str, Any]:
        return {"ok": True, "specs": len(self.items), "items": list(self.items)}

    def _validate(self, source: str, target: str) -> Dict[str, Any]:
        if not source or source.strip() != source:
            return {"ok": False, "error": "invalid_source"}
        if not target or target.strip() != target:
            return {"ok": False, "error": "invalid_target"}
        if ".." in target or "\x00" in target:
            return {"ok": False, "error": "unsafe_target"}
        return {"ok": True}

import time
from typing import Any, Dict, List


class SourceSpecValidator:
    """Validator for review-only source specs."""

    allowed_kinds = {"import_source", "refresh_source", "select_ref"}

    def __init__(self, kernel: Any = None):
        self.kernel = kernel
        self.results: List[Dict[str, Any]] = []

    def validate(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        if not spec or spec.get("mode") != "review_only":
            return self._result(False, "invalid_spec", spec)
        if spec.get("kind") not in self.allowed_kinds:
            return self._result(False, "kind_not_allowed", spec)
        if not spec.get("source") or not spec.get("target"):
            return self._result(False, "source_target_required", spec)
        return self._result(True, "valid", spec)

    def status(self) -> Dict[str, Any]:
        valid = len([item for item in self.results if item["valid"]])
        return {"ok": True, "checks": len(self.results), "valid": valid, "invalid": len(self.results) - valid}

    def _result(self, valid: bool, reason: str, spec: Dict[str, Any]) -> Dict[str, Any]:
        result = {"valid": valid, "reason": reason, "spec": spec, "created_at": time.time()}
        self.results.append(result)
        if self.kernel is not None and hasattr(self.kernel, "emit"):
            self.kernel.emit("source_spec_validator.checked", result)
        return {"ok": True, "valid": valid, "result": result}

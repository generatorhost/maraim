import time
from typing import Any, Dict, Iterable


class RealSourceReadiness:
    """Readiness record for source adapter promotion."""

    def __init__(self, kernel: Any = None):
        self.kernel = kernel
        self.records = []

    def add(self, name: str, source_type: str, checks: Iterable[str]) -> Dict[str, Any]:
        record = {
            "name": name,
            "source_type": source_type,
            "checks": list(checks),
            "ready": bool(name and source_type and list(checks)),
            "created_at": time.time(),
        }
        self.records.append(record)
        return {"ok": True, "record": record}

    def status(self) -> Dict[str, Any]:
        ready = [item for item in self.records if item["ready"]]
        return {"ok": True, "records": len(self.records), "ready": len(ready), "blocked": len(self.records) - len(ready)}

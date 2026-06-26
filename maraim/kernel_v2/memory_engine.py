import time
from typing import Any, Dict, List


class MemoryEngine:
    def __init__(self, kernel: Any):
        self.kernel = kernel
        self.working: List[Dict[str, Any]] = []
        self.long: List[Dict[str, Any]] = []
        self.semantic: List[Dict[str, Any]] = []
        self.procedural: List[Dict[str, Any]] = []
        self.episodic: List[Dict[str, Any]] = []
        self.collective: List[Dict[str, Any]] = []
        self.dna: List[Dict[str, Any]] = []

    def remember(self, space: str, item: Dict[str, Any]) -> Dict[str, Any]:
        target = getattr(self, space, None)
        if target is None or not isinstance(target, list):
            return {"ok": False, "error": "memory_space_not_found", "space": space}
        record = dict(item)
        record.setdefault("timestamp", time.time())
        record.setdefault("space", space)
        target.append(record)
        self.kernel.emit("memory.recorded", {"space": space, "count": len(target)})
        return {"ok": True, "space": space, "record": record}

    def recall(self, space: str, limit: int = 10) -> Dict[str, Any]:
        target = getattr(self, space, None)
        if target is None or not isinstance(target, list):
            return {"ok": False, "error": "memory_space_not_found", "space": space}
        return {"ok": True, "space": space, "items": target[-limit:]}

    def remember_experience(self, experience: Dict[str, Any], lesson: Dict[str, Any]) -> Dict[str, Any]:
        self.remember("episodic", {"type": "experience", "data": experience})
        self.remember("procedural", {"type": "lesson", "data": lesson})
        if lesson.get("recommendation"):
            self.remember("dna", {"type": "evolution_recommendation", "data": lesson})
        return {"ok": True, "experience_id": experience.get("id"), "lesson_id": lesson.get("id")}

    def status(self) -> Dict[str, Any]:
        return {
            "working": len(self.working),
            "long": len(self.long),
            "semantic": len(self.semantic),
            "procedural": len(self.procedural),
            "episodic": len(self.episodic),
            "collective": len(self.collective),
            "dna": len(self.dna),
        }
